# HW-0 run sheet: C900 / Hiwear Plus first contact

**STATUS: DRAFT, NOT APPROVED.** Written 2026-10-13 (Phase 1b, C900-Q15) as a document only. Nothing here has been run. Every session needs the owner's written go-ahead, recorded in OPEN-QUESTIONS, before step HW-2.1.

Sources: `tasks/HW-RECON.md`, skill `re-hardware-recon`, `recon-v2.md` §3, PROTOCOL §2-3, C900-Q14 (bond conditions).

## 0. Ground rules
- **Writes: 0** in this whole sheet. No GATT write, no write descriptor except the single CCCD on `...0003` in HW-3.
- **Never touch** (no read, no notify, no write): service 0xFF00 (0xFF01-03), service 0x18A8 (0x2AA8/0x2AA9), service `6E40FF01-B5A3-F393-E0A9-E50E24DCCA9E` (`...FF02/FF03`). The data service ends in `...DCCA9F`; the OTA one ends in `...DCCA9E`. Check the last letter before each step.
- No vendor app on the test phone during HW-2/HW-3 (it would bind and sync). **Turn Bluetooth off on the owner's phone** (or force-stop Hiwear Plus): the watch usually accepts one central, and the phone would reconnect and take it. Watch charged above 50 %.
- **Never unbind, reset or "remove device"** to make the watch visible. If it does not advertise while bound, stop and record that; it is a result.
- **No pairing agent:** on Linux run with no `bluetoothctl` agent registered (or `agent off`), so a pairing request fails and is seen instead of being auto-accepted. On macOS the system shows a dialog: press Cancel and treat it as an abort trigger.
- **Do not use `tools/notify_log.py` as-is for HW-3**: it subscribes to every notifiable characteristic, OTA ones included. Use the single-UUID snippet in HW-3.
- **Address on macOS:** CoreBluetooth gives a per-host UUID, not the MAC; record it as `UUID-masked` and do not paste it.
- **MAC masking:** in every pasted log and result file write the address as `XX:XX:XX:XX:AB:CD` (last two octets only). Keep the full address only in the shell variable `ADDR`. Mask the scan-record MAC bytes the same way.
- Machine: Linux or macOS with Python 3 and `bleak` installed (`pip install bleak`). Set `ADDR=` after the scan.

## 1. Budget
| Item | Limit |
|---|---|
| GATT writes | 0 characteristic writes. Descriptor writes: exactly 1 (the CCCD enable on `...0003` in HW-3) |
| Connections | 3 total (HW-2.2 one, HW-2.3 one retry allowed, HW-3 one) |
| Characteristic reads | 6 (0x2A19, 0x2A26, 0x2A27, 0x2A28, plus one repeat of each of two) |
| Session length | 30 min total; any single connection at most 3 min |

## 2. Abort triggers (stop, disconnect, power the watch down only through its own menu if needed, write down what happened)
- An **unexpected bond / pairing prompt** on the computer or the watch (C900-Q14: the app bonds only when the watch sends 0x0C key 19 or 0x0E key 1, or sets feature b15 0x40; a prompt here means the watch asks on its own).
- A **disconnect loop**: more than 2 drops within one step.
- **Any OTA, update, or "upgrading" screen** on the watch.
- The watch reboots, resets, or loses its time or face.
- Any tool output naming 0xFF00 / 0x18A8 / `...DCCA9E` as subscribed or written.
- Budget exhausted.

## HW-1 (optional, owner only): vendor-app snoop
Owner follows `docs/guides/HCI-CAPTURE-ANDROID.md`. Not part of this sheet's runs; if a log exists, parse it first (`python tools/btcap.py btsnoop_hci.log`) and compare with the expectations below before HW-2.

## HW-2. Passive scan, connect, discover, read (writes 0)
| # | Action | Expected [tag] | Tick | Paste |
|---|---|---|---|---|
| 2.1 | Watch on its pairing / QR screen. `python -c "import asyncio,bleak;print(asyncio.run(bleak.BleakScanner.discover(10,return_adv=True)))"`. Record name, RSSI, manufacturer data, service UUIDs. | Name [U] (FACTS §1 lists only [W] guesses). The app matches the MAC followed by `12 34` somewhere in the raw scan record [C, `BleScanActivity`]; bleak shows parsed fields only, so look in manufacturer data and service data, and if not found note "raw record not visible with bleak" (a capture or `btmon` shows the raw bytes). May need several scans | | |
| 2.2 | Connect (no pair flag), list services and characteristics; disconnect. | Services: `6E400001-...DCCA9F` (write `...0002` w/o response, notify `...0003`), 0x180F, 0x180A, plus the OTA services (list only, do not touch) [C] | | |
| 2.3 | Reconnect; read 0x2A19, 0x2A26, 0x2A27, 0x2A28 once each; disconnect. | 0x2A19 one byte = percent [C]. 0x2A27 = hardware version string. 0x2A26 firmware string. 0x2A28 feature map, byte 0 = 0xAA, length at least 26 when b25 is present [C]. If byte 0 is not 0xAA the app would ask cmd 0x19 instead (not sent here) | | |
| 2.4 | From the 0x2A28 bytes note b1 0x80 (isBLE3), b15 0x40 (isSupportPair), b25 0x80 (HR auto test + DND hidden). | Values [U]; record as [H] | | |

## HW-3. Listen on `...0003` only (writes 0 apart from the CCCD)
Snippet (subscribes to one UUID, prints time, length, hex; no other calls):
```python
import asyncio, os, time, bleak
U = "6e400003-b5a3-f393-e0a9-e50e24dcca9f"
async def main():
    async with bleak.BleakClient(os.environ["ADDR"]) as c:
        t0 = time.time()
        await c.start_notify(U, lambda _, d: print(round(time.time()-t0, 2), len(d), d.hex()))
        await asyncio.sleep(120)
asyncio.run(main())
```
| # | Action | Expected [tag] | Tick | Paste |
|---|---|---|---|---|
| 3.1 | Run the snippet 120 s. During it: press the watch button once, open heart rate on the watch, tap "find phone" if present, raise wrist. | Possibly nothing (the app starts sync by sending bind; we do not). Any frame should start `DF` (command) or `FD` (ack) with the checksum rule of PROTOCOL §4 [C]. Find phone = 0x0C key 1; camera shutter = 0x0C key 2 [C] | | |
| 3.2 | Note any 0x0C key 19 or 0x0E key 1 frame. | These are the bond triggers (C900-Q14); seeing one answers Q03 device side [H] | | |

## 2b. Tool hazard
`tools/notify_log.py` subscribes to every notifiable characteristic including OTA ones. Fix proposed as DRAFT task C900-Q17; until it lands, use only the snippet above.

## 3. On deviation
- Expected value differs (name, services, 0xAA marker, frame start): stop at the end of the step, paste output, record as [H] with the result file as source, open a contradiction row in FACTS; do not continue to the next step on the same session.
- A frame not in PROTOCOL §7: record it raw, do not reply.
- Any abort trigger: stop the whole session; next session needs a new approval.

## 4. Results
Write `tasks/results/run-sheet-<date>.md` with ticks, masked pastes, and the [H] facts; then update FACTS/PROTOCOL per HW-RECON "After hardware tasks".
