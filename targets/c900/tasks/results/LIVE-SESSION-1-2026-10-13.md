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
| **Q01 Scan Record Marker** | Company ID `0x314C`, manufacturer data `xxxxxxxxxxxx1234` (6-byte MAC followed by `12 34`) | [H] | Screen table (matches PROTOCOL.md §3 [C]) |
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
2026-10-13T13:37:33 SCAN device name=<redacted len=11> rssi=-53 mac=5301...712B mfg=314c:len=8:xxxx..
...
2026-10-13T13:37:33 SCAN done count=13
2026-10-13T13:37:33 PROBE_END
```

Screen table observation (owner terminal, not logged):
- Target entry: `<CB-UUID masked>  rssi=-53  name='Watch Ultra'  mfg=314c:xxxxxxxxxxxx1234 (6 masked MAC bytes then 12 34)`
- Manufacturer bytes contain the exact watch MAC (`XX:XX:XX:XX:XX:XX`) followed by `12 34`.

---

## 4. Step 4: Inspect Run

Command executed by owner:
```bash
.venv-probe/bin/python tools/c900_probe.py inspect --address <CB-UUID masked> --listen 30
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

---

## 6. Review and corrections (Claude, 2026-10-13, from the committed logs only)
The run is real and clean: exit 0 both steps, 0 abort triggers, 0 writes beyond one CCCD. Corrections to the text above:

1. **Privacy.** The CoreBluetooth UUID and the full watch MAC were written in sections 3-4; masked in this commit. They remain in git history (f4f37cd, LOG at the same commit); history rewrite is the owner's call.
2. **"3 OTA services" is wrong.** Only 0xFF00 (FF01/FF02) is a known OTA service [C, PROTOCOL section 2]. 0x18A8 and `...DCCA9E` are **absent** [H]. **0xFF10** (char FFF1 write) and **0xFF12** (FF13 write, FF14 notify) are not in PROTOCOL; purpose [U]. The probe's `ota_services_seen=3` counted FF00 and its two characteristics, not FF10/FF12. Both are writable, so the probe now denies them (fail closed) until static work identifies them.
3. **Version byte: the probe was right to refuse, and the fix is not "accept more digits".** The app keeps the integer before the first dot (C900-Q04): `"10000"` -> 10000, stored in the byte `PROTOCOL_VERSION` -> **0x10** [I, int-to-byte cast; smali check pending]. The probe sends 0x01. Session 2 is **blocked** until (a) smali confirms the cast and (b) the codec takes ver as input, or (c) a capture shows the real ver byte. `protocol_major` now parses `10000` and safe-write refuses with `ver_byte=0x10`.
4. **Q03 is narrowed, not settled.** Seen [H]: no bond request and no pairing dialog during 30 s idle, without bind. Not tested: after bind or after a time-sync ack. Feature byte 15 = 0xE6 has 0x40 set, so the vendor app **would** call createBond after the time-sync ack (I-30 [C]). The `time` command is therefore the riskiest of the three session 2 commands.
5. **Q01 settled [H]:** BLE name `Watch Ultra` (same as the Classic name), manufacturer company 0x314C, data = own MAC followed by `12 34`, which matches the app's scan rule (a) [C].
6. **Absent [H]:** 0x2A24 and 0x2A29. 0x2A25 present (8 bytes, redacted). 0x2A26 = 0x2A27 = `10000`.
7. **Feature map decode** (bit names from C900-Q05 [C], values [H]): b1 0xCF (BLE3, contacts, 12/24 h, unit, language, SpO2; no temperature); b14 0x10 (SOS); b15 0xE6 (0x80, pairing 0x40, drink 0x04, new message table 0x02); b16 0x41 (OTA 0x40); b18 0xCF (RGB565, 8-byte face code, binPreviewFlag **clear**, 7-day weather, user name, DIY wallpaper); b25 0x00.
8. "No anti-RE" stands for what was observed: nothing hostile in 30 s of idle listen and the GATT table. That is a narrow sample, not a general verdict.
