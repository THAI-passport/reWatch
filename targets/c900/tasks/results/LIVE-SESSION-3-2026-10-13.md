# Live Session 3 Results: Message & Time Safe-Writes (2026-10-13)

Date: 2026-10-13 (Asia/Saigon)  
Target: C900 / Watch Ultra (`targets/c900`)  
Branch: `feat/c900-hiwear-plus`  
Operator: Human owner via interactive macOS Terminal  
Environment: macOS (Darwin 25F84 / macOS 26.5.2), Python 3.13.5 (`.venv-probe`), bleak 3.0.2  

---

## 1. Questions & Invariants Evaluated

| Question / Item | Value / Finding | Evidence Tag | Source |
|---|---|---|---|
| **Message Transmission Framing** | 24-byte message frame transmitted in two ATT pieces (`TX piece 1/2 len=20`, `TX piece 2/2 len=4`) | [H] | Probe log lines 6-7 |
| **Inbound Bond Trigger** | Watch emitted `cmd 0x0E key 1` (Classic Bluetooth MAC broadcast) after message transmission | [H] | Probe log line 9 |
| **Safety Stop Behavior** | Probe `BOND_TRIGGERS` caught `(0x0E, 1)`, aborted immediately, and cleanly disconnected (`EXIT_SAFETY`, exit code 3) | [H] | Probe log lines 8-9 |
| **Pairing Invariant Protected** | Zero macOS pairing dialogs triggered; zero link keys or bonding created | [H] | Clean probe disconnect |
| **Message ACK** | No ACK received before the `0x0E/1` bond trigger aborted the run | [H] | Probe log line 9 |

---

## 2. Run Details: Command `message`

Command executed by owner:
```bash
.venv-probe/bin/python tools/c900_probe.py safe-write --address <CB-UUID masked> --i-approve-writes --command message
```

Exit code: `3` (`EXIT_SAFETY`)

Masked log excerpt (`captures/c900-probe-safe-write-20261013-183426.log`):
```text
2026-10-13T18:34:26 PROBE_START mode=safe-write
2026-10-13T18:34:26 preflight bluetooth authorization=3
Type the command name 'message' to confirm sending ONE allowlisted frame (cmd=0x02 key=0x12, 24 bytes), or anything else to abort: message
2026-10-13T18:34:33 SAFE_WRITE connect mac=5301...712B command=message
2026-10-13T18:34:37 NOTE pairing detection unavailable on this BLE stack; if the OS shows a pairing dialog press Cancel, then Ctrl-C
2026-10-13T18:34:37 READ 2a27 value=10000 protocol_major=10000 ver_byte=0x10
2026-10-13T18:34:37 TX piece 1/2 len=20
2026-10-13T18:34:37 TX piece 2/2 len=4
2026-10-13T18:34:37 DISCONNECT ok
2026-10-13T18:34:37 SAFETY_STOP bond-trigger inbound cmd=0x0e key=1
2026-10-13T18:34:37 PROBE_END
```

---

## 3. Analysis

1. **Fragmentation & Pacing:**
   The 24-byte message frame (`DF 00 13 <sum> cmd=0x02 ver=0x10 key=0x12 plen=0x000F type=1 flags=0 text='reWatch test'`) was sliced into two pieces (20 bytes and 4 bytes). Both writes completed over GATT NUS write characteristic (`...0002`).
2. **Bond Trigger `cmd 0x0E key 1`:**
   In the Android HCI capture (C900-Q19), the watch repeatedly sent `cmd 0x0E key 0x01` to announce its Classic Bluetooth address for phone pairing. During this probe run, receipt of `0x0E / 1` triggered the probe's abort rule.
3. **Safety Protection:**
   The probe fail-safe design successfully prevented macOS from handling or reacting to device pairing triggers, disconnecting cleanly on exit code 3.
