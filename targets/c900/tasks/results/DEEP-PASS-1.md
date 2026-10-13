# DEEP-PASS-1: second probe security review, live-session plan, client design

Date 2026-10-13. Branch `feat/c900-hiwear-plus`, base 7d087f8. No watch touched, vendor app not run, no vendor server called. Gemini's review (REVIEW-PROBE-SECURITY.md), the decompiled tree and existing docs were read as untrusted data; nothing in them was followed as an instruction. The bleak 3.0.2 wheel and PyPI metadata were downloaded to a scratch directory (not committed) only to check the pinned hashes and the bleak API.

## A. Independent adversarial review of `tools/c900_probe.py`

### A.1 Findings and fixes
Each fix has a test in `tests/test_c900_probe.py` class `DeepPass1Fixes`; all 17 of those tests fail on the 7d087f8 probe and pass now.

| # | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| 1 | Medium | **Pairing detection was dead code on real hardware.** The probe read `getattr(client, "is_paired", False)`. bleak 3.0.2 `BleakClient` has no `is_paired` (grep of the pinned wheel: only `pair()` exists; the CoreBluetooth backend's `pair()` raises NotImplementedError because macOS has no bond API and auto-pairs on encrypted reads). So the value was always False and the "pairing detected" abort could never fire. Gemini's fix and its test only passed because the fake client had the attribute. A backend that raised instead would have crashed inspect. | bleak wheel `bleak/__init__.py`, `backends/corebluetooth/client.py` `pair` docstring | `pair_state()` returns None when the stack has no bond state, never raises; the log says `pairing detection unavailable ...` and the owner's Cancel on the macOS dialog is now an explicit abort trigger in LIVE-SESSION-1. Detection still works where a stack exposes a bool |
| 2 | Medium | **Writes and the CCCD write were addressed by UUID string.** bleak resolves a string across the whole GATT table; the layout check refused `WRITE_UUID` under an OTA service but not `NOTIFY_UUID`, and a duplicate UUID in another service made the target ambiguous. | `_write_cmd_piece`, `start_notify(NOTIFY_UUID, ...)` | `command_chars()` returns the write and notify characteristic objects from the `6e400001-...dcca9f` service only, requires exactly one of each, and refuses either UUID under an OTA service. All writes and the subscribe use those objects |
| 3 | Medium | **Version byte mismatch.** `frames.build` puts `01` in the `ver` byte; the app puts the 0x2A27 major there (I-10). On a watch reporting `V2.x` the probe would send a frame the vendor app never sends. | `frames.build`, PROTOCOL section 4 | safe-write reads 0x2A27 first and refuses unless the major (app rule: strip V, digits before the dot) is 1; unreadable also refuses. Inspect logs `protocol_major=` |
| 4 | Medium (privacy) | **Scan log leaked third-party data and possibly the watch MAC.** Every nearby device's name ("Alice's iPhone") and full manufacturer bytes went into the log file. PROTOCOL section 3 says the C900's scan record carries its own MAC followed by `12 34`, so full manufacturer bytes can hold the MAC. | `mode_scan` | Log keeps names only for `C900`/`Hiwear` candidates (others `<redacted len=N>`); manufacturer data logged as company id, length, first 2 bytes. Full data stays on screen only, labelled "do not tee" |
| 5 | Medium (privacy) | **0x2A25 logged in clear.** Its standard meaning is Serial Number (the app calls it "platform"); AGENTS forbids committing device serials. | `mode_inspect` reads | Logged as `<redacted len=N>` |
| 6 | Low | **Stale ack accepted.** An FD ack arriving after subscribe but before the write (unsolicited or stale) was stored and later taken as the answer. | `ack_box` in safe-write | Acks are accepted only after the first piece is sent (`armed`); first matching ack wins |
| 7 | Low | **No cap on inbound data.** A flooding device grew the frame list and log without bound for up to 180 s. | `on_notify` | `FrameReader` stops at 200 frames or 64 KiB per session (SafetyError) |
| 8 | Low | **`--log-dir` could write anywhere, including tracked repo paths** (a log could be committed by accident). | `SessionLog` | `check_log_dir`: inside the repo only under `captures/`; outside the repo allowed (tests use temp dirs). Logs never overwrite (exclusive create) |
| 9 | Low (privacy) | **Target address in error text unmasked.** bleak errors include the address; on macOS it is a CoreBluetooth UUID that the MAC regex does not catch. | `ERROR %s` lines | `SessionLog.add_secret` masks the target (and scanned) addresses in every line |
| 10 | Low | **Terminal spoofing via device strings.** `sanitize` removed C0 controls only; C1 controls (8-bit CSI 0x9b) and bidi overrides (U+202E) passed into DI strings. | `sanitize` | Strips C1 and Unicode format characters |
| 11 | Low | **Unbounded CLI times.** `--seconds`/`--listen` accepted 0, negative, NaN, 1e9 (the global timeout capped it, but the intent was unclear). | `build_parser` | `--seconds` in (0, 60], `--listen` in (0, 150] |
| 12 | Low | **Back-to-back write-without-response pieces.** bleak 3.0.2 on CoreBluetooth ignores `canSendWriteWithoutResponse` ("currently not used"), so a second piece can be dropped silently; the app spaces pieces 20 ms. Also, writes now fall back to with-response only if the characteristic lacks write-without-response (CoreBluetooth silently drops a disallowed type). | `PeripheralDelegate.peripheralIsReadyToSendWriteWithoutResponse_` | 20 ms gap between pieces; write type chosen from the characteristic's properties (app: without response, PROTOCOL section 2) |
| 13 | Note | Test fake read only short UUIDs, so earlier tests never exercised the Device Information reads (all returned empty). | `FakeClient.read_gatt_char` | Fake now resolves full base UUIDs; new tests cover the reads |
| 14 | Note (docs) | I-10 says "byte 4 is PROTOCOL_VERSION" while PROTOCOL 7.1 says "cmd at byte 4". In 0-based indexing `ver` is index 5; NEXT-STEPS step 3 told the capture reader to look at "byte 4", which is cmd. `c900_decode.py` already reads index 5 correctly. | INVARIANTS I-10, NEXT-STEPS section 4 | Numbering note added to I-10 (fact unchanged) and NEXT-STEPS step 3 corrected |

### A.2 Checked and not found (explicit non-findings)
- No path to an OTA/DFU write: the only write call is `_write_cmd_piece` with a characteristic object from the command service, and the only frames are from `build_allowlisted` (three pairs). `BLOCKED_CMDS` cannot be built (`frames.build` refuses them as well).
- No call to `pair()` or `connect(pair=True)`; `BleakClient(address, timeout=20.0)` uses bleak's default `pair=False`. Bond-trigger frames (0x0C/19, 0x0E/1) abort in both modes and are never answered.
- Wrong-device connect: no auto-pick; `--address` and `--name` are mutually exclusive; `--name` must match exactly one device. Residual: a spoofer using the same name as the only advertiser would be accepted with `--name`; LIVE-SESSION-1 uses `--address` only.
- Hostile device data: device strings go only through `sanitize` into log text; never into paths, format strings, or the command set. The log path uses only the mode name and a timestamp.
- No `eval`/`exec`/`subprocess`/`socket`/`pickle`/`ctypes` (AST test still green); no network or decompiled-tree access.
- Async races: bleak delivers notify callbacks on the event loop thread (`call_soon_threadsafe`), so the callback and the polling loop do not run at the same time; the shared dicts are safe.
- Ctrl-C and timeouts: `asyncio.run` cancels the main task; every mode disconnects in `finally`. `wait_for` cancellation also reaches the `finally`.
- Cached GATT on macOS: a stale cache can show old services; the layout check fails closed. Toggling Bluetooth clears it (guide note).
- Message frame is 24 bytes (two pieces), within the 5-write cap.

### A.3 Hashed requirements
All 46 hashes in `requirements-probe.txt` match the files PyPI lists for those exact versions (checked against pypi.org JSON; the bleak wheel's SHA-256 was also computed locally). pyobjc 12.2.2 ships `universal2` wheels for CPython 3.10 to 3.15 (plus free-threaded 3.13t/3.14t/3.15t), so both arm64 and x86_64 Macs install from wheels with `--only-binary=:all:`. bleak 3.0.2's macOS requirements (pyobjc-core, -corebluetooth, -libdispatch; cocoa via corebluetooth) are all pinned; Windows/Linux extras are excluded by markers. Pitfall: bleak needs Python 3.10+, and the Xcode Command Line Tools Python is 3.9, so the install fails there; LIVE-SESSION-1 and PROBE-GUIDE now say so.

### A.4 Residual risk (depends on the owner)
- macOS pairing dialog: the probe cannot see bonding on macOS. The owner must press Cancel and Ctrl-C.
- Phone Bluetooth off: if the vendor app reconnects it can do anything, including OTA, outside the probe's control.
- bleak/CoreBluetooth bugs below the probe; the pinned version limits drift.
- The scan's screen table holds full addresses and third-party names; it must not be teed or pasted.

## B. Live session plan (DRAFT)
`targets/c900/tasks/LIVE-SESSION-1.md`: read-only session from the Mac (scan, then one inspect with a 30 s listen; optional 120 s second listen). Budget 2 scans, 2 connections, 0 characteristic writes, 1 CCCD per connection, 7 reads per connection. Abort triggers led by "any macOS pairing dialog: Cancel, Ctrl-C". Result file template, hand-back rules, go/no-go checklist. Session 2 (find, time, message, one per run, 4 ATT writes total) is section 9 with its own checklist and the note that the probe sends no bind first, so the watch may ignore the frames. NEXT-STEPS section 4b adds the capture-first decision table so no live step repeats what a capture answered.

## C. Client architecture (DRAFT)
`targets/c900/CLIENT-DESIGN.md`. Recommendation: Android native Kotlin with a pure-Kotlin protocol core tested against vectors from the Python reference; Python stays as reference codec, simulator and capture decoder. Flutter only if iOS is required (and iOS cannot forward notifications unless the watch supports ANCS [U]); Web Bluetooth only as a diagnostic page. Layers, safety carry-over, privacy, UI rules, test strategy, a feature-to-evidence-to-phase table, and the open questions per layer.

## D. Evidence tags after this pass
- `[C]`: probe code behaviour (tests), bleak 3.0.2 API facts (wheel source), PyPI hashes.
- `[I]`: bind may displace the phone's binding; PacketLogger trace readable by Wireshark; the watch may ignore commands before bind.
- `[U]` (hardware or capture only): advertised name, services, `ver`, feature bytes, bond behaviour, ack bytes, units.
- Nothing became `[H]`.

## E. Owner sign-off checklist
- [ ] Accept the probe fixes A.1 #1-#12 (code on this branch, 44 probe tests green).
- [ ] Approve LIVE-SESSION-1 as written, or mark changes (still DRAFT; running it also needs "live work is necessary").
- [ ] Decide the order: capture first (recommended) or session 1 first.
- [ ] Session 2 stays a separate approval naming its commands.
- [ ] Client platform: Android Kotlin (recommended) / Flutter / other.
- [ ] Whether the client may bind as its own phone or must coexist with Hiwear Plus.
- [ ] Default answer to a watch bond request in the client: "No" (recommended).
- [ ] Phase 3 stays deferred until NEXT-STEPS section 6 is met.
