# Adversarial Security and Correctness Review: C900 Bluetooth Probe

Date: 2026-10-13 (Asia/Saigon)  
Target: `tools/c900_probe.py`  
Branch: `feat/c900-hiwear-plus`  
Evaluated against: `INVARIANTS.md` (I-13, I-14, I-20, I-30, I-50, I-51, I-54, I-55), `PROTOCOL.md` (§2, §4, §5), `PROBE-SECURITY.md`, `client/c900/frames.py`, `requirements-probe.txt`.  
Testing: static analysis and fake-bleak unit tests only (no real radio, no device contact).

---

## 1. Findings

### Finding 1: Broken OTA lookalike write check and missing parent service check
- Severity: High
- Evidence: `tools/c900_probe.py:301-303` (original):
  `if cu.endswith("0002") and cu.endswith(OTA_SERVICE_SUFFIX): raise SafetyError(...)`
- Exploit / failure story:
  A 128-bit UUID like `6e400002-b5a3-f393-e0a9-e50e24dcca9e` ends in `dcca9e` (`OTA_SERVICE_SUFFIX`); it does not end in `"0002"`. Requiring both with `and` was impossible to satisfy, leaving the hard refuse guard completely dead. Furthermore, `_require_command_layout` checked `cu == WRITE_UUID` without verifying that the parent service `su` was not an OTA service. An anomalous peripheral defining `WRITE_UUID` under an OTA service (`0xFF00`, `0x18A8`, or `...dcca9e`) would pass layout validation and allow Bleak to issue writes to a characteristic under an OTA service.

### Finding 2: Incomplete 5610 DFU/OTA UUID matching in `is_ota_uuid`
- Severity: Medium
- Evidence: `tools/c900_probe.py:117-135` (original)
- Exploit / failure story:
  Per Invariant I-14 and the security mission, any UUID containing "5610" must be treated as OTA/DFU (Bluetrum 5610). If a device advertised a vendor-specific 128-bit UUID containing `5610` (e.g. `12345610-1111-2222-3333-444455556666`), `u.startswith("0000")` evaluated to `False`, `short` was empty, and `is_ota_uuid` returned `False`. Additionally, for 32-bit UUIDs such as `000018a8`, `u.endswith("0000")` evaluated to `False`, failing proper extraction of the 16-bit short ID.

### Finding 3: Missing pairing/bonding detection loop in `mode_safe_write`
- Severity: High
- Evidence: `tools/c900_probe.py:476-528` (original) vs `mode_inspect:412-414`
- Exploit / failure story:
  `mode_inspect` captured `paired_before` and checked `(not paired_before) and bool(getattr(client, "is_paired", False))` inside its polling loop. `mode_safe_write` never stored `paired_before` and never checked `client.is_paired` while awaiting the command ACK. Per Invariant I-30, when the watch receives `cmd 0x02 key 0x01` (time sync), if feature bit 15 `0x40` is set, bonding is expected by the vendor firmware. If the watch or macOS Bluetooth stack triggered pairing during `safe-write`, the probe failed to abort and allowed pairing to proceed unmonitored.

### Finding 4: Frame desynchronization in `on_notify` blinds bond-trigger aborts
- Severity: High
- Evidence: `tools/c900_probe.py:341-346, 465-470` (original)
- Exploit / failure story:
  If a single corrupted or leading byte (e.g. `\x00`) preceded a frame in `buf`, `total` was calculated from non-header bytes `(buf[1] << 8) | buf[2] + 4`. If those bytes formed a large integer, the while loop broke because `len(buf) < total`. Because non-header bytes were not dropped, `buf` became permanently locked. Subsequent inbound frames (such as bond triggers `0x0C` key 19 or `0x0E` key 1, or ACKs) were appended but never parsed, blinding the probe's abort guards.

### Finding 5: Personal data leak in `redact_line`
- Severity: Medium
- Evidence: `tools/c900_probe.py:108-114` (original)
- Exploit / failure story:
  When a log line contained personal information keywords (`message push`, `caller`, `location`) without the exact substring `"payload"`, `s.split("payload", 1)[0]` returned the entire original string `s`, simply appending `payload=<redacted>` to the unredacted personal information. Furthermore, `_MAC_FULL` matched only 6-octet colon-separated MACs; on macOS (CoreBluetooth), peripheral addresses are 128-bit UUIDs, which were left unmasked.

### Finding 6: Non-atomic write cap enforcement on cap exhaustion
- Severity: Medium
- Evidence: `tools/c900_probe.py:488-508` (original)
- Exploit / failure story:
  Line 491 used `pass` instead of raising `SafetyError`. If transmitting a command required more writes than remaining in `budget.writes`, transmission began anyway and failed mid-frame when `budget.charge_write()` hit `MAX_WRITES`. This left the watch in an undefined partial-frame state rather than refusing the write atomically before any byte was sent.

### Finding 7: Missing error handling in `mode_safe_write` notification callback
- Severity: Low
- Evidence: `tools/c900_probe.py:474-486` (original)
- Exploit / failure story:
  In `mode_inspect`, `on_notify` caught exceptions and set `abort["reason"]`. In `mode_safe_write`, `on_notify` had no `try...except` wrapper. An exception raised in the callback thread became an unhandled Bleak background task error, leaving the main loop hanging until `ACK_TIMEOUT_S`.

### Finding 8: Conflicting CLI target flags not mutually exclusive
- Severity: Low
- Evidence: `tools/c900_probe.py:426-430, 565-571` (original)
- Exploit / failure story:
  Supplying both `--address <A>` and `--name <B>` caused `_resolve_target` to silently ignore `--name`. If the flags pointed to different devices, the probe connected without warning the operator.

### Finding 9: Non-recursive path traversal filtering in `sanitize`
- Severity: Low
- Evidence: `tools/c900_probe.py:93` (original)
- Exploit / failure story:
  Input like `....//` became `../` after single-pass replacement. A regex pattern `re.sub(r"\.\.+[/\\]", "", s)` provides robust defense in depth.

### Finding 10: Adversarial prompt injection defense audit
- Severity: Note
- Evidence: `tools/c900_probe.py:31-35, 77-96`, `INVARIANTS.md:61-62`
- Exploit / failure story:
  Audited all files and confirmed that the probe treats APK trees and device-supplied strings strictly as untrusted data: no `eval`/`exec`/`subprocess`, no dynamic imports, all constants are hardcoded and reviewed against invariants.

---

## 2. Proposed Fixes & Applied Patches

All fixes applied directly to `tools/c900_probe.py` and `tests/test_c900_probe.py` on branch `feat/c900-hiwear-plus`:
1. Updated `is_ota_uuid` with `"5610" in u` and proper 32-bit UUID short extraction.
2. In `_require_command_layout`, ensured `have_write` and `have_notify` can only be fulfilled by non-OTA services. Added immediate refusal if `WRITE_UUID` or any characteristic starting with `6e400002` resides under an OTA service or ends with `OTA_SERVICE_SUFFIX` (`dcca9e`).
3. Added active `is_paired` polling in `mode_safe_write`'s wait loop.
4. Stream resynchronization in `on_notify`: drops leading non-header bytes until `0xDF` or `0xFD` is encountered; bounds frame size between 9 and 1024 bytes.
5. Atomic write cap check: raises `SafetyError` before transmission if `budget.writes + len(pieces) > MAX_WRITES`.
6. Robust personal data redaction in `redact_line` for `message push`, `caller`, and `location` entries regardless of the `"payload"` keyword.
7. Made `--address` and `--name` mutually exclusive in `build_parser`.
8. Added 6 new unit test suites in `tests/test_c900_probe.py` covering all fixes (23 tests total, all passing).

---

## 3. Residual Risk

1. **macOS Pairing UI:** If the watch initiates link-layer pairing, CoreBluetooth prompts the user. The probe will disconnect once `is_paired` flips, but the owner must dismiss the OS prompt.
2. **Coexisting Phone Connection:** The owner must turn phone Bluetooth off; otherwise the vendor app will connect concurrently and could trigger OTA/unbind.
3. **CoreBluetooth GATT Caching:** macOS caches GATT databases across reconnections; stale tables require toggling Bluetooth in System Settings.

---

## 4. Explicit Non-Findings

- **No Remote Code Execution:** No `eval`, `exec`, `subprocess`, `pickle`, `ctypes`, or dynamic module loading.
- **No Blocked Command Transmission:** `build_allowlisted` strictly restricts commands to `time`, `message`, and `find`. `BLOCKED_CMDS` (`0x01, 0x04, 0x06, 0x07, 0x0D, 0x13`) cannot be constructed.
- **Inspect Mode Zero Writes:** `mode_inspect` only reads `DI_UUIDS` and enables CCCD on `...0003`.
- **Pinned Package Surface:** `requirements-probe.txt` uses exact version pins and full PyPI wheel SHA-256 hashes (`--require-hashes`).
