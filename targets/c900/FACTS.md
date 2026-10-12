# Fact sheet: C900 watch

Single place for values that sources disagree on. Other documents link here. Tags: [C] app code (Hiwear Plus 2.0.1), [W] third party, [I] inferred, [U] unknown, [owner] owner statement.

## 1. Identity
| Topic | Value | Tag | Superseded or conflicting value |
|---|---|---|---|
| Companion app | Hiwear Plus, `com.myled.HiwearPlus` | [owner] plus [W] (Play listing; C900 Ultra2/Ultra3 retail pages name it) | HryFine `com.yscoco.watch` and HiWatch Pro `com.jusheng.hiwatchpro` (landscape doc, earlier TARGET): superseded |
| Vendor | Shenzhen United Power Technology (lianhezhuli) | [W] listing, [C] `com.lhzl` packages and `lianhezhuli` hosts | |
| Chip family | Bluetrum | [C] for the app's tooling, [I] for the watch | landscape doc: Bluetrum or Jieli [W]; Gemini doc: AB5610B or BT8958B [W]; no Jieli code in the app [C] |
| Screen | 240x296, 2.09 inch (C900 Ultra2/Ultra3 retail) | [W] | landscape doc 240x286 or 320x385 [W]; Gemini 240x286 or 320x385 [W] |

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
| No bonding | stated | no createBond in app code | consistent [C], device side [U] |
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
