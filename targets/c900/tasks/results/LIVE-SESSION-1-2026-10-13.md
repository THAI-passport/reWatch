# Live Session 1 Results: Read-Only First Contact (2026-10-13)

Date: 2026-10-13 (Asia/Saigon)  
Target: C900 / Watch Ultra (`targets/c900`)  
Branch: `feat/c900-hiwear-plus`  
Operator: Human owner via interactive macOS Terminal  
Environment: macOS (Darwin 25F84 / macOS 26.5.2), Python 3.13.5 (.venv-probe with bleak 3.0.2 pinned hashes), checkout commit `8cdeb32`  
Logs cited:
- Scan: `captures/c900-probe-scan-20261013-133720.log`
- Inspect: `captures/c900-probe-inspect-20261013-133934.log`

---

## 1. Questions Settled by Live Session 1

| Question | Value / Finding | Evidence Tag | Source |
|---|---|---|---|
| **Q01 Advertised Name** | `'Watch Ultra'` | [H] | `c900-probe-scan-20261013-133720.log` / screen table |
| **Q01 Scan Record Marker** | Company ID `0x314C`, manufacturer data `4142d0xxxxxx1234` (6-byte MAC followed by `12 34`) | [H] | Screen table (matches PROTOCOL.md §3 [C]) |
| **Q02 GATT Services** | Command service `6e400001-b5a3-f393-e0a9-e50e24dcca9f` (`0002` write, `0003` notify); Battery `0x180F`; Device Info `0x180A`; OTA services `0xFF00`, `0xFF10`, `0xFF12` (untouched) | [H] | `c900-probe-inspect-20261013-133934.log` lines 5-10 |
| **PROTOCOL_VERSION (0x2A27)** | Read raw value `"10000"`. `protocol_major` returned `None` because the probe's regex `r"(\d{1,3})(?:\.|$)"` expected up to 3 digits (e.g. `V1.2`) while firmware returned a 5-digit build string `"10000"`. | [H] | `c900-probe-inspect-20261013-133934.log` line 14 |
| **Firmware Version (0x2A26)** | Read raw value `"10000"` | [H] | `c900-probe-inspect-20261013-133934.log` line 13 |
| **Serial Number (0x2A25)** | `<redacted len=8>` | [H] | `c900-probe-inspect-20261013-133934.log` line 12 |
| **Battery Level (0x2A19)** | `61%` | [H] | `c900-probe-inspect-20261013-133934.log` line 17 |
| **Feature Map (0x2A28)** | Marker `0xAA`, len 27, hex `aacfe081dff6fc3800000000000010e64108cf1400000000000000`. Parsed flags: `isBLE3=True`, `isSupportPair=True`, `hideHrAndDnd=False`. | [H] | `c900-probe-inspect-20261013-133934.log` line 15 |
| **Q03 Inbound Bond / Traffic** | Zero frames received during 30 s listen (`frames=0`); no bond requests initiated by watch; no macOS pairing prompts triggered. | [H] | `c900-probe-inspect-20261013-133934.log` line 19 |

---

## 2. Go / No-Go Checklist Verification

- [x] Owner wrote "live work is necessary" for this session in OPEN-QUESTIONS (date: 2026-10-13, scope = LIVE-SESSION-1 only).
- [x] Option A selected and recorded in OPEN-QUESTIONS: `Watch Ultra` disconnected in macOS System Settings -> Bluetooth (Classic link idle; risk of LE cross-transport key derivation acknowledged in writing).
- [x] Checkout is `feat/c900-hiwear-plus` at commit `8cdeb32`; `python3 -m unittest discover -s tests` passes.
- [x] Python 3.13.5 in `.venv-probe` with pinned hashes from `requirements-probe.txt`.
- [x] Terminal app has macOS Bluetooth permission.
- [x] Watch charged above 50% (measured 61% via GATT `0x2A19`), bound to Hiwear Plus (not unbonded), showing normal face.
- [x] Phone Bluetooth turned off (no contention).
- [x] 30 minutes free; owner executed steps directly in Terminal.

---

## 3. Step 3: Scan Run

Command executed by owner:
```bash
python tools/c900_probe.py scan --seconds 12
```

Exit code: `0`

Masked log excerpt (`captures/c900-probe-scan-20261013-133720.log`):
```text
2026-10-13T13:37:20 PROBE_START mode=scan
2026-10-13T13:37:20 SCAN start seconds=12 (read-only, no connect)
2026-10-13T13:37:33 SCAN device name='' rssi=-45 mac=6D23...796B mfg=
...
2026-10-13T13:37:33 SCAN device name=<redacted len=11> rssi=-53 mac=5301...712B mfg=314c:len=8:4142..
...
2026-10-13T13:37:33 SCAN done count=13
2026-10-13T13:37:33 PROBE_END
```

Screen table observation (owner terminal, not logged):
- Target entry: `5301DFC1-xxxx  rssi=-53  name='Watch Ultra'  mfg=314c:4142d013d7cc1234`
- Manufacturer bytes contain the exact watch MAC (`41:42:D0:xx:xx:xx`) followed by `12 34`.

---

## 4. Step 4: Inspect Run

Command executed by owner:
```bash
.venv-probe/bin/python tools/c900_probe.py inspect --address 5301DFC1-xxxx --listen 30
```

Exit code: `0`

Masked log excerpt (`captures/c900-probe-inspect-20261013-133934.log`):
```text
2026-10-13T13:39:34 PROBE_START mode=inspect
2026-10-13T13:39:34 INSPECT connect mac=5301...712B listen=30s
2026-10-13T13:39:37 NOTE pairing detection unavailable on this BLE stack; if the OS shows a pairing dialog press Cancel, then Ctrl-C
2026-10-13T13:39:37 LAYOUT ok command-service present; ota_services_seen=3 (untouched)
2026-10-13T13:39:37 SERVICE 0000180f-0000-1000-8000-00805f9b34fb chars=00002a19-0000-1000-8000-00805f9b34fb[notify,read]
2026-10-13T13:39:37 SERVICE 0000180a-0000-1000-8000-00805f9b34fb chars=00002a25-0000-1000-8000-00805f9b34fb[read];00002a27-0000-1000-8000-00805f9b34fb[read];00002a26-0000-1000-8000-00805f9b34fb[read];00002a28-0000-1000-8000-00805f9b34fb[read]
2026-10-13T13:39:37 SERVICE 0000ff10-0000-1000-8000-00805f9b34fb chars=0000fff1-0000-1000-8000-00805f9b34fb[write-without-response,write]
2026-10-13T13:39:37 SERVICE 0000ff12-0000-1000-8000-00805f9b34fb chars=0000ff13-0000-1000-8000-00805f9b34fb[write];0000ff14-0000-1000-8000-00805f9b34fb[notify,read]
2026-10-13T13:39:37 SERVICE 6e400001-b5a3-f393-e0a9-e50e24dcca9f chars=6e400003-b5a3-f393-e0a9-e50e24dcca9f[notify,read];6e400002-b5a3-f393-e0a9-e50e24dcca9f[write-without-response,write]
2026-10-13T13:39:37 SERVICE 0000ff00-0000-1000-8000-00805f9b34fb chars=0000ff01-0000-1000-8000-00805f9b34fb[notify,read];0000ff02-0000-1000-8000-00805f9b34fb[write-without-response,write]
2026-10-13T13:39:37 READ 2a24 error=Characteristic 00002a24-0000-1000-8000-00805f9b34fb was not ...
2026-10-13T13:39:37 READ 2a25 value=<redacted len=8>
2026-10-13T13:39:37 READ 2a26 value=10000
2026-10-13T13:39:38 READ 2a27 value=10000 protocol_major=None
2026-10-13T13:39:38 READ features marker=0xaa len=27 bits={'isBLE3': True, 'isSupportPair': True, 'hideHrAndDnd': False} hex=aacfe081dff6fc3800000000000010e64108cf1400000000000000
2026-10-13T13:39:38 READ 2a29 error=Characteristic 00002a29-0000-1000-8000-00805f9b34fb was not ...
2026-10-13T13:39:38 READ battery=61%
2026-10-13T13:39:38 LISTEN start uuid=...e50e24dcca9f seconds=30 (CCCD write is the only write)
2026-10-13T13:40:09 LISTEN done frames=0
2026-10-13T13:40:09 DISCONNECT ok
2026-10-13T13:40:09 PROBE_END
```

---

## 5. Abort Triggers and Anomaly Evaluation

- **Abort Triggers Hit:** 0. No macOS pairing request, no watch pairing prompt, no disconnect loops, no OTA interaction.
- **Watch Physical State:** Remained on normal watch face; battery at 61%; no reboot, no time loss, no unbind.
- **Anti-RE / Malicious Behavior:** None detected. Zero unexpected packets, zero prompt injection strings. The firmware exhibited standard Bluetrum BLE peripheral behavior.
- **Tooling Finding for `tools/c900_probe.py`:**
  - `protocol_major` currently parses via `re.match(r"(\d{1,3})(?:\.|$)", s)`. Because the device returned a 5-digit build string `"10000"` for `0x2A27`, `protocol_major` returned `None`. This needs refinement in `tools/c900_probe.py` before any Phase 2 safe-write can proceed.
