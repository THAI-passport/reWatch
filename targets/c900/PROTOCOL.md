# Protocol: C900 watch (companion app Hiwear Plus)

Artifact: `com.myled.HiwearPlus` 2.0.1 (version code 31), hashes in SOURCES.md. Static reading only. Tags: [C] seen in the decompiled app (class named so it can be found again; no code copied), [V] emulator or vector against app code, [H] hardware, [W] third party, [I] inferred, [U] unknown. Disputed values live in FACTS.md.
Owner statement 2026-10-13: the C900 pairs with Hiwear Plus [owner-reported; not protocol evidence, not [H]].
Earlier text of this file assumed HryFine and a third-party layout; it is kept in `sources/legacy-t900-c900-PROTOCOL.md` (superseded).

## 1. Stack identification
- Vendor: Shenzhen United Power Technology ("lianhezhuli", web domain lhzl666.com) [W listing]; app packages `com.myled.HiwearPlus` (UI and BLE layer) and `com.lhzl.*` (sport, database, skin, speech) [C].
- BLE library: welie BLESSED (`com.welie.blessed`) [C]. No Jieli (`com.jieli`, `libjl_*`), Realtek, Nordic DFU or Telink SDK present [C, package and library search].
- Chip family: Bluetrum. Evidence: the Bluetrum `abpartool` native library and Java wrapper (image to "par" format for watch faces), and a separate firmware-update path named after the Bluetrum "5610" OTA service 0x18A8 [C]. [I] the C900 sold with this app is Bluetrum based; the exact SoC is [U].
- Shared backend with HryFine: the app's update check calls an `api/hry/...` endpoint on the vendor's OTA host [C]. [I] Hiwear Plus and HryFine share a vendor SDK; protocol identity with HryFine is not proven (HryFine was not decompiled).
- The Beambox BadgeSdk watch device tag 0xB9 does not appear; no manufacturer-tag table of that kind exists in this app [C].

## 2. Transports [C, `BleConstants`]
| Use | Service | Characteristics | Write type | Tag |
|---|---|---|---|---|
| Commands and data | NUS-like `6E400001-B5A3-F393-E0A9-E50E24DCCA9F` | write `...0002`, notify `...0003` | without response | [C] |
| Battery | 0x180F | 0x2A19 (notify used) | - | [C] |
| Device info | 0x180A | 0x2A26 firmware, 0x2A27 hardware, 0x2A25 "platform", 0x2A28 "function" | read | [C] |
| Firmware OTA, generic (NEVER TOUCH) | 0xFF00 | 0xFF01 notify, 0xFF02 write, 0xFF03 | - | [C] |
| Firmware OTA, Bluetrum 5610 (NEVER TOUCH) | 0x18A8 | 0x2AA8 notify, 0x2AA9 write | - | [C] |
| Another OTA service (NEVER TOUCH) | `6E40FF01-B5A3-F393-E0A9-E50E24DCCA9E` | `...FF02`, `...FF03` | - | [C] |
Note: the data service ends in `...DCCA9F`, the OTA service in `...DCCA9E` [C].

## 3. Scan and connect [C, `BleScanActivity`, `MBleManager`]
- The scan is unfiltered (BLESSED `scanForPeripherals`). A device is listed when it has a name and either (a) the raw scan record, printed as colon-separated hex, contains the device's own MAC followed by `12:34`, or (b) MAC followed by `56:10` (DFU mode), or (c) the name starts with `B0`, `H2` or `HY`.
- No product name such as C900 is matched; the advertised name of a C900 is [U] (HW-2).
- After service discovery the app reads the 5610 OTA characteristic to detect DFU mode, then requests MTU 32 normally (450 in DFU mode; the OTA tool path requests 185). App data writes are cut into 20-byte pieces regardless of MTU, 20 ms apart. Each full 20-byte piece gets up to two retries 100 ms apart; the final remainder piece gets one retry after 20 ms; a frame of 20 bytes or less is written once with no retry. A failed write disconnects at once [C smali, C900-Q04].
- No `createBond` call in the app's own code [C]; BLESSED reacts to bonding if the watch asks [C library]; whether the C900 asks is [U].
- **Conflict (C900-Q05, see FACTS §4):** smali shows three app-code `createBond` sites (`BleDataUtils.setDeviceContro` on inbound 0x0C key 19, `BleDataUtils.setSettingSuccess`, `MainActivity$4.run`). Not resolved here.
- Bind: command 3 key 0 with an 8-character random id saved per phone; unbind: command 4 key 0 [C, `GeneralUtils`].

## 4. Framing [C, `IssuedUtil`, `NotifyWriteUtils`, `AckPackageConfigUtils`]
App to watch: `DF | len_hi len_lo | sum | cmd | ver | key | plen_hi plen_lo | payload`.
- `ver` is `IssuedUtil.PROTOCOL_VERSION`: default `0x01`, overwritten on connect with the integer major version from the 0x2A27 read (leading `V`/`v` stripped) [C, `IssuedUtil`, `NotifyWriteUtils.onRead`]. Only the hand-built `setAutoUpdate` frame hard-codes `01`. The C900's value is [U] (HW-2).
- len = payload length + 5 (counts cmd through payload); total = len + 4.
- sum = low byte of the sum of all other bytes (signed bytes, then & 0xFF; same result as unsigned mod 256).
Acknowledgement: `FD 00 05 sum cmd key x_hi x_lo status`, status 1 = success. The app's ACK to a good inbound frame is `x = 0, status 1`; its NAK to a bad-sum frame is `x = 3, status 0` [C smali, `NotifyWriteUtils.dataHandle`]. The watch's acks are read at bytes 4, 5 and 8 only; the watch's own x value is [U].
Watch to app: same `DF` frame; the app reassembles notifications until len + 4 bytes, checks the sum, replies with an `FD` ack (status 1), then dispatches on cmd.
Flow: one command in flight; the next waits for the ack; no ack within **100 s** disconnects [C smali: `const-wide/32 0x186a0` in the send runnable and `resetTimeout`, C900-Q04]. The timer is armed only for 0xDF frames while the main screen exists; a NAK re-arms it. The command channel is paused while an OTA transfer runs (`isOTA`).

## 5. Commands (app to watch) [C unless marked]
| cmd | Name in app | Keys seen (purpose) |
|---|---|---|
| 0x01 | OTA (old) | firmware path, not studied for use |
| 0x02 | settings | 1 time sync, 2 alarms, 3 step goal, 4 profile, 5 sedentary, 6 wearing hand, 7 notification switches, 8 power save, 9 raise-to-wake, 10 matching, 11 find watch (1 on, 0 off), 12 camera mode (1 on, 0 off), 13 heart switch, 14 blood pressure switch, 15 sleep window, 17 call state, 18 message push, 24 temperature window, 25 temperature switch, others |
| 0x03 / 0x04 | bind / unbind | key 0 |
| 0x05 | sport data | watch to app health records |
| 0x06 / 0x0D | reset / factory restore | never used by the client |
| 0x07 | factory test | never used |
| 0x08, 0x09 | alarm list, settings query | key 0 |
| 0x0A | flash read | not studied |
| 0x0F | watch face | 1 query, 3 select face by code, 4 (after sync), 5 custom face layout, 10 set code to update |
| 0x11, 0x12, 0x14 | drink, message-remind, sedentary queries | key 0 |
| 0x13 | OTA (new) | 1 info, 2 start: firmware path, NEVER used |
| 0x0B, 0x0C | device test, device control | 0x0B never used; 0x0C inbound find-phone/camera (see §7) |
| 0x0E | BT 3.0 info | app key 3 request; watch keys 1 (classic MAC), 4 (contact MD5) |
| 0x19 | device features | key 0 query |
| 0x1A | functions | 3 social, 5 payment, 7 power-save support queries; 9 power save set; 21 exit find-phone; 23 altitude; 24 location |
| 0x1B | assistant (chat) | not needed |
### 5.1 Key and payload tables (C900-Q04) [C]
Full per-key layouts, with source methods and smali checks, are in `tasks/results/C900-Q04.md`. Summary of cmd 0x02 keys: 1 time, 2 alarms (5 B each, same date packing + serial<<3 + repeat), 3 step goal u32, 4 profile (sex/age/height/weight bit-packed), 5 sedentary, 6 hand (1 left, 2 right), 7 notify switches (11-13 B), 8 power save, 9 raise-to-wake window, 10 pairing (2 start, 1 stop), 11 find watch, 12 camera, 13 heart, 14 BP, 15 sleep window, 17 call state, 18 message (type table in Q04 §5), 20 DND window, 21 language, 22 heart auto, 24 temp auto, 25 temp switch, 26 12/24 h, 27 units, 28 SpO2, 29 today weather, 30 temp unit, 31 SOS, 33 drink, 34 new notify switches (20 B), 35 7-day weather, 36 user name, 38 payment code, 39 social code, 58 all-day light-up, 59 all-day DND. Windows are minute-of-day u16 BE.
Other cmds: 0x05 keys 1/6/10 (history, real-time steps, today); 0x0E key 3 (BT 3.0 info request); 0x19 key 0 (features); 0x1A keys 3/5/7 (support queries), 9 (power save set), **21 exit find-phone**, 23 altitude/pressure, 24 location. jadx printed wrong constant names for several of these keys; the values above are from smali.

Time sync payload (cmd 2 key 1): 4 bytes packing, high bit first, year-2000 (6 bits), month (4), day (5), hour (5), minute (6), second (6) [C, `SettingIssuedUtils.settingSysTime` smali: `add-int/lit16 v2, v2, -0x7d0` confirms the year offset is exactly -2000 / 0x7d0]. Packing in client: `client/c900/frames.time_payload`.
Message push (cmd 2 key 18): `type, 0, 0, UTF-8 text` with text "title:body" cut at 196 bytes [C].

## 6. Watch faces and OTA-channel transfer [C; no client sending]

Documented for the protocol only. Client rule: no watch-face upload, no OTA write, and no firmware path until a reviewed design and owner approval (ground rule 7). `BLOCKED_CMDS` in `client/c900/frames.py` also refuses the command-channel OTA ids.

### 6.1 Store face (`.bin` from the vendor) [C, `DialDetailActivity.startPush` / `getFileBuffer`]
1. Download lands as `<filesDir>/dial/<name>.bin`.
2. The file is opened as text (line by line). The text is an obfuscated Base64 string: `StringUtils.decodeInfo` replaces three MD5-of-literal tokens with `=`, `+`, `/` then Base64-decodes (`decodeInfoToBytes`). Token seeds (own MD5, documented so a rebuild can verify): `ZZ22` -> `37396d18...f110` (=), `Z22Z` -> `f9319252...8abd` (+), `XGHJ` -> `34657488...062a` (/).
3. Unless `BleDataUtils.binPreviewFlag` is set, the buffer is trimmed to a length read from the decoded header: index `i = ((b[16]-b[17]-1)*20)`, then little-endian u32 at `i+22..i+25` via `HexUtil.byte2IntLR`; clamp to `[1, len]`. That trimmed buffer is what is transferred.
4. Transfer uses `OTAUtils(context, main=5, sub=1, bytes, ...)` (CommandUtils.CMD_WATCH_FACE = 5, START_OTA / PAPER-style sub 1).

### 6.2 Custom / DIY background [C, `WatchFaceEditActivity.compressParData`]
- Bitmap -> raw RGBA via `ImageUtils.getRawImageData`, then Bluetrum native `ParTool.rawToPar(raw, w, h, false, false, false)`.
- Result stored in `BitmapUtils.bmp565Bytes` (name is historical; content is the PAR blob). If larger than `WatchFaceBean.getDefaultPaperSize()`, JPEG quality steps down by 5 until it fits or quality hits 5.
- Upload path: `OTAUtils(..., main=2, sub=1, ...)` (CommandUtils.CMD_PAPER = 2). Time layout on the face still uses command-channel cmd 0x0F key 5.

### 6.3 OTA-channel framing on service 0xFF00 / write 0xFF02 / notify 0xFF03 [C, `CommandUtils`, `OTAUtils`, `OTANotifyWriteUtils`]
Separate from the DF/FD command channel. Headers are signed bytes -43 / -42 (= 0xD5 / 0xD6).

Control frame (app -> watch), `CommandUtils.generalSendBytes`:
`D5  main  sub  fun  00  00  plen_hi  plen_lo  [payload...]  sum`
- `sum` = (sum of every byte including a zero at the sum slot) mod 256, written in the last byte.
- `startOTA(main, sub, fun=1, mtu-3, file_len)` payload is 6 bytes: `mtu_hi mtu_lo len_be32`.
- Group CRC: fun=2, payload 1 byte (running CRC of the group).
- File CRC: fun=3, payload 1 byte (running CRC of the whole file).
- Reboot: fun=4, no payload (skipped after main in {2,4,5} so paper / contact / watch-face transfers do not reboot).

Data frame (app -> watch): `D6` + up to `(deviceMtu - 1)` bytes of file. Chunks are not ACKed individually; the group CRC is.

Session [C, `OTAUtils` / `OTANotifyWriteUtils`]:
1. Request MTU 185; disable command-channel notify; after 2 s enable OTA notify. 60 s overall timeout disconnects.
2. On OTA-ready: write `startOTA`. Watch replies with a D5 control whose fun (byte 3) is `0x81`; payload carries `deviceMtu` (u16), `sendInterval` ms (u16, default 300 if 0; field init is 500), `groupPacNum` (u8), timeout units (u8 * 5000 ms).
3. Split file into packets of `deviceMtu - 1`. Group them by `groupPacNum`. For each group: write each `D6`+chunk (CRC8-style running xor poly 0x31 left-shift, same for per-group and whole-file CRC), then fun=2 CRC; watch fun=`0x82` status 0 means next group. After last group: fun=3 file CRC; watch fun=`0x83` status 0 finishes. Error header D6 on notify, or status != 0, aborts.
4. On finish for main in {2,4,5}: restore MTU 32 and re-enable command notify. Otherwise send reboot.

CRC note [C, smali of `OTAUtils.sendData`]: for each byte `x` of a chunk, both the group accumulator and the file accumulator do `acc ^= x` then 8 rounds of `(acc << 1) ^ 0x31` if the high bit was set else `acc << 1`. Only the low 8 bits are sent.

### 6.4 Cus5610 / DFU path (not used for dial push) [C, inventory]
`Cus5610CommandUtils` / `Cus5610OTAUtils` speak a different D5 framing (fun codes for partition / 4K check / dial area / reboot) over the Bluetrum DFU service `0x18A8`. Dial and paper push above use the generic OTAUtils path on 0xFF00, not Cus5610. No further detail until a firmware task is approved.

### 6.6 Contacts (verified, C900-Q08) [C, `ContactActivity.saveAsFile`, `MainActivity$6`, `CommandUtils`]
Contacts have **no DF command-channel opcode**. They ride the OTA channel above as `OTAUtils(main=4 = CMD_CONTACT, sub=1)`, confirmed in smali at both call sites (contacts screen and the `syncContact` broadcast receiver). OTA-channel main ids: 1 OTA, 2 paper, 3 log, 4 contact, 5 watch face [C, `CommandUtils.smali`]. File sent = `MD5(body, 16 bytes) || body`; body = `count(u8) 00`, then per contact `off_lo off_hi name_len num_len` (cumulative u16 LE offset into the string area), then UTF-8 `name||number` per contact; names cut to 30 bytes. Capability: 0x2A28 byte0 `0xAA`, `byte1 & 0x40` contacts, `byte14 & 0x08` 200-contact. The watch reports its list MD5 on inbound cmd 0x0E key 4 (see §7). Client must not implement (C900-D05). Detail: `tasks/results/C900-Q08.md`.

### 6.5 What stays [U]
- Exact PAR container layout (native `libabpartool`; only the first 16 bytes are logged by the app).
- Whether every C900 dial.bin uses the trim rule or `binPreviewFlag`.
- Wire confirmation of MTU / groupPacNum values the C900 returns.

## 7. Inbound (watch to app) [C, `NotifyWriteUtils`, `BleDataUtils.setSettingSuccess`]
`DF` frames with cmd 5 (health and sport records), settings and alarm replies, find-phone requests, camera shutter; `FD` acks with cmd 2 (settings keys), 3 (bind ok), 4 (unbind ok) and others; battery level on 0x2A19.

Ack-driven follow-ups during the sync sequence [C, `BleDataUtils.setSettingSuccess`]: on bind/settings acks the app may createBond if unbound, write cmd 0x0E key 3, push profile / username, request settings info (cmd 9), sport target, and time sync (cmd 2 key 1). Exact key map for every inbound DF payload is still being tabulated (S5).

### 7.1 Inbound map, first pass (C900-Q05, partial) [C, `NotifyWriteUtils.dataHandle`, `BleDataUtils`]
cmd at byte 4, key at byte 6, payload from byte 9. Mapped: 0x05 health (field map pending); 0x08 alarm list; 0x09 settings reply (field map pending); **0x0C device control**: 1/15 find phone start/stop, 3/4 watch camera open/close, **8 bind accepted** (byte 9 = 1 first bind), **9 bind refused** (app disconnects), 10-13 media keys, 18 BT status, 19 bond request; 0x0E BT 3.0 info (1 classic MAC, 4 contact MD5); 0x0F face replies; 0x11 drink; 0x12 new notify switches; 0x13 OTA-new status (never used); 0x14 sedentary; **0x19 feature map** (same as 0x2A28, byte 0 = 0xAA); 0x1A support bitmaps and location requests; 0x1B assistant events. Full table and the feature bit map: `tasks/results/C900-Q05.md`.

## 8. Server endpoints (inventory only, no calls) [C]
Vendor API via Retrofit (about 70 endpoints): login and account binding, `member_devices/bind_mac`, `dial/get_list`, `dial/get_detail`, `dial_local/get_list`, `order/get_onwer_dials`, `census/add_dial_down`; OTA host with `api/hry/get_update`, `api/ota/down_finish`, `api/ota/down_error`; two weather hosts; privacy pages. No secret values recorded here.

## 9. Worked examples (own arithmetic from the [C] rules)
- Settings query, cmd 9 key 0, no payload: `DF 00 05 EE 09 01 00 00 00` (0xDF + 0x05 + 0x09 + 0x01 = 0xEE) [V against the rule as read from code; not seen on a wire].
- Time sync, cmd 2 key 1, 2026-10-13 14:05:30: payload `6A 9A E1 5E`; full frame built by `frames.build(0x02, 0x01, time_payload(...))` [V against smali packing; not seen on a wire].

## 10. Unknowns and the test that settles each
| Unknown | Test |
|---|---|
| C900 advertised name and whether the scan record has MAC + 12 34 | HW-2 read-only scan |
| Which of the GATT services the C900 exposes | HW-2 read-only service list |
| Whether the watch requires bonding | HW-2 |
| Exact PAR container bytes (native lib) | optional native RE; not needed for first contact |
| C900's returned OTA MTU / groupPacNum | HW-1 capture or approved OTA session |
| Time year offset in smali | done: -0x7d0 [C] |
| Whether Hiwear Plus and HryFine use the same opcodes | decompile HryFine (optional) |
