# Fact sheet: C900 watch

Single place for values that sources disagree on. Other documents link here. Tags: [C] app code (Hiwear Plus 2.0.1), [W] third party, [I] inferred, [U] unknown, [owner] owner statement.

## 1. Identity
| Topic | Value | Tag | Superseded or conflicting value |
|---|---|---|---|
| Companion app | Hiwear Plus, `com.myled.HiwearPlus` | [owner] plus [W] (Play listing; C900 Ultra2/Ultra3 retail pages name it) | HryFine `com.yscoco.watch` and HiWatch Pro `com.jusheng.hiwatchpro` (landscape doc, earlier TARGET): superseded |
| Vendor | Shenzhen United Power Technology (lianhezhuli) | [W] listing, [C] `com.lhzl` packages and `lianhezhuli` hosts | |
| Chip family | Bluetrum | [C] for the app's tooling, [I] for the watch | landscape doc: Bluetrum or Jieli [W]; Gemini doc: AB5610B or BT8958B [W]; no Jieli code in the app [C] |
| Screen | 240x296, 2.09 inch (C900 Ultra2/Ultra3 retail) | [W] | landscape doc 240x286 or 320x385 [W]; Gemini 240x286 or 320x385 [W] |

### 1.1 Hardware facts (LIVE-SESSION-1 2026-10-13, owner Mac, results/LIVE-SESSION-1-2026-10-13.md)
| Topic | Value | Tag | Note |
|---|---|---|---|
| BLE name | `Watch Ultra` (Classic name identical) | [H] | Gemini's C900/Watch-Call/Hiwear-* names not seen |
| Scan record | company 0x314C, data = own MAC + `12 34` | [H] | matches app scan rule (a) [C] |
| Services | NUS `...DCCA9F`, 0x180F, 0x180A, 0xFF00, **0xFF10**, **0xFF12**; no 0x18A8, no `...DCCA9E` | [H] | FF10/FF12 purpose [U], denied in probe |
| 0x2A26 / 0x2A27 | `10000` / `10000` | [H] | app ver byte would be 0x10 [I], not 1 |
| 0x2A28 | `aacfe081dff6fc3800000000000010e64108cf1400000000000000` (27 B) | [H] | b15 0x40 set: app bonds after time-sync ack (I-30) |
| Idle behaviour | 0 frames in 30 s, no bond request | [H] | without bind |

## 2. Disputes with the Gemini document (`sources/gemini-hiwear-re.md`)
| Topic | Gemini says | App code says | Verdict |
|---|---|---|---|
| Service 0xFF00 / FF01 / FF02 | "vendor command service" | firmware OTA service | contradicted [C]; never touch |
| MTU | app requests 512 | 32 normally, 450 in DFU, 185 in the OTA tool; data cut in 20-byte pieces | contradicted [C] |
| Time sync | cmd 0x02 sub 0x0A, 6 bytes | cmd 0x02 key 1, 4 packed bytes | contradicted [C] |
| Device info | cmd 0xF3 sub 0x00 | no 0xF3 command; info from 0x180A reads and cmd 0x19/0x1A queries | contradicted [C] |
| 12/24 h | cmd 0x02 sub 0x01 | key 1 is time sync | contradicted [C] |
| Find device | cmd 0x07 | 0x07 is factory test; find watch is cmd 2 key 11 | contradicted [C]; 0x07 is dangerous |
| Camera | cmd 0x05 | 0x05 is sport data; camera is cmd 2 key 12 | contradicted [C] |
| Watch-face prep/chunk | cmd 0x04 key 1/2 | 0x04 is UNBIND; faces go over the OTA path | contradicted [C]; 0x04 would unbind the watch |
| Header and checksum | `DF`, len, sum with byte 3 zero, cmd, 01, sub, plen | same | confirmed [C] |
| Ack | `FD 00 05 sum cmd key len len status` | same layout; status 1 = ok | confirmed [C] |
| Gemini frame builder | total_len = 6 + payload | len = 5 + payload | contradicted [C]; its own table says "excluding first 4 bytes", which gives 5 |
| Advertised names C900, Watch-Call, Hiwear-* | names listed | app matches MAC+12:34 in the scan record or names B0/H2/HY | unverified [U]; HW-2 |
| No bonding | stated | **retired 2026-10-13** (REVIEW-PHASE1): app code calls `createBond` at 3 sites (see §4) | app side: Gemini claim contradicted [C]; device side [U] (C900-Q03) |
| Dial format ("ZL" or "AB_DIAL" magic, RGB565 at 0x100) | layout given | Bluetrum par conversion in native code; format not read | [U] |
| Hiwear is a reskin of HryFine | stated | shared `api/hry` endpoint and vendor | partly supported [I] |
| Sensors are synthetic | stated | not settled by app code | [W] |
| Bootloader layout, PB3 recovery pad | stated | not in the app | [W]; physical work needs owner approval |

## 3. Earlier claims (landscape doc, combined target) now annotated
| Claim | Status |
|---|---|
| C900 app is HryFine, NUS `...DCCA9F` data service | app superseded; the UUID itself is [C] in Hiwear Plus |
| Ack header 0xFD vs app 0xDF swap suspicion | resolved: both exist, DF = data both ways, FD = ack [C] |
| Length meaning (total = Len + 4) | confirmed [C] |
| Opcodes 0x02/0x0A time, 0xF3/0x00 info (used by `client/c900/frames.py`) | contradicted [C], see section 2 |
| OTA service 0x18A8 is dangerous | consistent; [C] that the app uses it only for firmware |

## 4. Confirmed this pass (2026-10-13, static)
| Claim | Tag | Evidence |
|---|---|---|
| Time year offset is exactly -2000 (0x7d0) | [C] | `SettingIssuedUtils.settingSysTime` smali: `add-int/lit16 v2, v2, -0x7d0` (jadx had printed `BaseResp.CODE_ERROR_PARAMS`) |
| Command ids match CommandID.smali | [C] | OTA 0x01, SETTING 0x02, BIND 0x03, UNBIND 0x04, RESET 0x06, FACTORY_TEST 0x07, DEVICE_SETTING 0x09, WATCH_FACE 0x0F, OTA_NEW 0x13, RESTORE 0x0D |
| Dangerous ids never built by client | [C] | `client/c900/frames.BLOCKED_CMDS = {0x01,0x04,0x06,0x07,0x0D,0x13}` |
| Dial `.bin` is obfuscated Base64 text, not raw bytes | [C] | `DialDetailActivity.startPush` + `StringUtils.decodeInfo` |
| Watch-face / paper / contact push rides OTAUtils on 0xFF00 with D5/D6 framing | [C] | `OTAUtils`, `CommandUtils` (main 5/2/4); CRC poly 0x31 |
| Cus5610 (0x18A8) is a separate DFU path, not used for dial push | [C] | `Cus5610CommandUtils` inventory only |
| Repo holds the pinned XAPK zip (owner exception) | [C] | `resources/c900/hiwear-plus-2.0.1.xapk.zip` LFS; SOURCES `REPO_COPY` |
| Contacts use OTA channel `main=4` (CMD_CONTACT), sub 1; no DF opcode | [C] | `ContactActivity.saveAsFile` + `MainActivity$6` smali consts; `CommandUtils.smali` (C900-Q08) |
| OTA-channel main ids: 1 OTA, 2 paper, 3 log, 4 contact, 5 watch face | [C] | `CommandUtils.smali` (`CMD_LOG=3` was not documented before) |
| Ack timeout is 100 s | [C] | smali `const-wide/32 0x186a0` in `NotifyWriteUtils` send runnable + `resetTimeout` (C900-Q04); jadx value confirmed |
| Frame byte 4 is `PROTOCOL_VERSION` (default 1, set from 0x2A27 major), not a fixed `01` | [C] | `IssuedUtil.getSendByte` smali `sget-byte PROTOCOL_VERSION`; corrects earlier PROTOCOL §4 and the `frames.FIXED_BYTE` comment. C900 value [U] |
| App NAK to a bad-sum inbound frame: `FD 00 05 sum cmd key 00 03 00` | [C] | `NotifyWriteUtils.dataHandle` smali (`v11=0x3`, `v4=0x0`); earlier text said app acks always use x=0 |
| Send retries: only full 20-byte pieces get 2x100 ms retries; last piece 1x20 ms; <=20-byte frames none | [C] | send runnable smali consts 0x14 / 0x64; earlier PROTOCOL §3 said two retries per piece |
| cmd 0x1A key 21 = exit find-phone, not a language query | [C] | `GeneralUtils.reqeustExitFindPhone` smali `0x1a`/`0x15`; jadx printed `KEY_SETTING_SET_LANGUAGE` |
| SimWatch ack x = `00 01` in `client/c900/frames.ack()` | [I] | not from code; app ignores bytes 6-7 of watch acks. Fix in Phase 3 |
| **RESOLVED 2026-10-13** App code calls `BluetoothDevice.createBond` (conditionally) | [C] smali | smali: `BleDataUtils.setDeviceContro` (0x0C key 19, BOND_NONE only), `BleDataUtils.setSettingSuccess`, `MainActivity$4.run`. Earlier "no createBond" was a negative search result on jadx output; three named positive smali hits outrank it (REVIEW-PHASE1). §2 row retired. Gaps: the trigger conditions of the `setSettingSuccess` and `MainActivity$4` sites are not mapped (C900-Q14). Re-check when the tree exists: `rg -n "BluetoothDevice;->createBond" targets/c900/work/smali \| grep -v welie` must print 3 lines. Device side still [U] (C900-Q03) |
| Bind accepted / refused arrive as inbound cmd 0x0C key 8 / key 9 | [C] | `BleDataUtils.setDeviceContro` (C900-Q05) |
| Feature map is delivered both by the 0x2A28 read and by the cmd 0x19 reply; byte 0 = 0xAA | [C] | `NotifyWriteUtils.dataHandle` case 25 -> `readFeatures` |
| cmd 2 key 26 payload 1 = 12 h, 0 = 24 h | [C] | sync sends `settingHourUnit(false)` with `isHour24 = false` |
| OTA `sendInterval`: 500 ms field init, 300 ms if the 0x81 reply has 0; **never used for pacing** | [C] | smali `OTANotifyWriteUtils.<init>` `0x1f4`, `dataHandle` `0x12c`; only read is a log line; `getSendInterval()` has no callers (C900-Q07). Earlier text read as a send interval |
| OTA D6 pacing = 10 ms sleep + write-complete callback | [C] | `OTANotifyWriteUtils` send runnable (`Thread.sleep(0xa)`) + `onWrite(true)` pops the queue |
| Inbound OTA D5 replies are not checksum-checked; status at byte 5; payload from byte 8 | [C] | `OTANotifyWriteUtils.dataHandle` |
| Server API: 70 Retrofit endpoints, 7 static hosts; dial download URLs dynamic; requests signed with MD5 `sign` (secret not recorded) | [C] | `Request.java`, `Urls.java`, `SignUtils` (C900-Q09). No server contacted |
| Dial trim: offsets 16/17/x20/+22..25 smali-verified; trim only on the store-face screen and only if the watch's `binPreviewFlag` (feature b18 0x20) is clear; purchased faces never trimmed | [C] | `DialDetailActivity.getFileBuffer` smali; `OwnerDialDetailActivity` (C900-Q06) |
| `HexUtil.byte2IntLR` is big-endian over its argument order; inbound sedentary threshold (0x14) is u16 BE, same as outbound | [C] | `HexUtil.byte2IntLR`; closes a C900-Q05 [U] |
| createBond conditions: 0x0C/19 (BOND_NONE); cmd 2 key 1 ack in sync + feature b15 0x40 -> MAC^0x55 last byte; 0x0E/1 classic MAC -> up to 3 tries, 35 s | [C] smali | C900-Q14 steps 4-5 (`xor-int/lit8 0x55`, `0xa`, `0xc`, `0x88b8`) |
| Feature b25 0x80 drives both `isShowHrAutoTest` and `isShowDnd` | [C] smali | `readFeatures` (`v4 = 0x80`, index `0x19`); C900-Q14 step 7 |
| cmd 5 field maps for keys 2, 4, 5, 9, 12, 13, 15 (offsets, widths, bounds) | [C] smali | C900-Q16 |
| Health date is 2 bytes: year-2000 = (b0&0x7F)>>1, month = (b0&1)<<3 \| b1>>5, day = b1&0x1F (differs from cmd 2 key 1 time packing) | [C] smali | `DevBaseDataUtils.getDateBean`; C900-Q16 |
| Steps-per-hour clamp: steps > 20000 sets calorie to 400000 (`0x61a80`; jadx shows `JCameraView.MEDIA_QUALITY_FUNNY`) | [C] smali | `StepUtils.getSportBy1Hour`; C900-Q16 |

## 5. Confirmed from Hardware Capture (2026-10-13, C900-Q19)
| Claim | Tag | Evidence |
|---|---|---|
| Wire version byte is 0x10 (app writes) / 0x01 (watch replies) | [H] | `captures/btsnoop_hci.log.last`: all 63 app TX frames carry `ver=0x10`; all watch frames carry `ver=0x01`. Matches `10000 & 0xFF == 0x10` cast |
| Watch sends unsolicited `cmd 0x0E key 0x01` (classic MAC) 3 times; triggers app `createBond()` | [H] frame | `captures/btsnoop_hci.log.last`: watch sends Classic BT MAC at t=4.811s, 16.731s, 34.492s; C900-Q19 §7 |
| Wire pairing status: 3 `HCI_Remote_Name_Request` commands timed out (status 0x04); zero Classic connections/auth and zero LE SMP/encryption events | [H] | `captures/btsnoop_hci.log.last`: C900-Q19 §7 |
| Bind handshake sequence is cmd 0x03 key 0 -> cmd 0x0C key 8 -> acks | [H] | `captures/btsnoop_hci.log.last`: t=1.959s - 2.548s |
| Watch ack x = total length of the acked frame (`plen + 9`), not a sequence | [H] | `captures/btsnoop_hci.log.last`: verified across all acknowledged commands (time sync x=13, matching x=10, token x=17, message x=37/22) |
| Time sync payload is the I-21 packed format (`6a9b05cb` = 2026-10-13 16:23:11), not a Unix timestamp | [H] | C900-Q19 section 6; reproduced by `frames.time_payload` |
