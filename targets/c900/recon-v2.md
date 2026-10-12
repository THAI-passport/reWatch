# C900 / Hiwear Plus — recon v2 (Phase 1 static results)

Date: 2026-10-13 (Asia/Saigon). Builds on [recon-v1.md](recon-v1.md). Static only (jadx `decompiled/` + apktool `work/smali/` of the pinned 2.0.1 build); no watch, no app run, no server call. Detail lives in `tasks/results/C900-Q0*.md`, PROTOCOL.md and FACTS.md.
Tags: [C] app code (smali-checked where marked), [V] local re-derivation, [I] inferred, [U] unknown.

## 1. Per question
| ID | State | Answer (one line) | Tag |
|---|---|---|---|
| Q08 | done | Contacts ride OTA `main=4, sub=1`; no DF opcode. File = MD5 + count + 4-byte index + UTF-8 strings | [C smali] |
| Q04 | done | 100 s ack timeout confirmed (`0x186a0`); full cmd 2 key table; byte 4 is `PROTOCOL_VERSION`; NAK x=3 | [C smali] |
| Q05 | **partial** | Inbound dispatch for 14 cmds, device-control keys (bind accept 0x0C/8, refuse 0x0C/9, find phone, camera, media), feature bits. Stopped on a FACTS conflict (createBond) | [C] |
| Q07 | done | 300 vs 500 resolved: 500 = field init, 300 = zero-reply substitute, **neither is used**; pacing is write-callback + 10 ms | [C smali] |
| Q09 | done | 70 endpoints, 7 hosts, MD5 `sign` scheme (secret not recorded) | [C] |
| Q06 | done | Trim offsets smali-verified; store screen only, gated by the watch's `binPreviewFlag` | [C smali] + [V] seeds |

## 2. Corrections to earlier text
| Earlier | Now | Source |
|---|---|---|
| Frame byte 4 is a fixed `01` | `PROTOCOL_VERSION`: default 1, set from the 0x2A27 major version | Q04 |
| Two 100 ms retries per piece | only for full 20-byte pieces; last piece one 20 ms retry; frames <=20 B none | Q04 |
| App acks always x = 0 | ACK x=0 status 1; NAK x=3 status 0 | Q04 |
| OTA interval default 300 / init 500 | both real, neither applied | Q07 |
| cmd 2 key 8 "basic setting" | power save on/off | Q04 |
| 0x1A key 21 (jadx: language) | exit find-phone | Q04 |
| No createBond in app code | **retired**: 3 app-code sites in smali (conditional); old row retired 2026-10-13 | Q05, FACTS §4, REVIEW-PHASE1 |

## 3. First-contact relevant (for HW-0 run sheet)
- Bind flow: app sends cmd 3 key 0 (8 ASCII chars); the watch answers **inbound 0x0C key 8** (accept; byte 9 = 1 first bind) or **key 9** (refuse, app disconnects). The app then sends cmd 2 key 10 (pairing start) [C].
- Feature map arrives twice: 0x2A28 read and cmd 0x19 reply; byte 0 = 0xAA. It decides payload variants (notify length, message type table, face code size, trim) [C].
- The watch may ask for classic bonding (0x0C key 19) and reports a classic BT MAC (0x0E key 1) [C]; whether the C900 does is [U] (Q03).
- 12/24 h: payload 1 = 12 h, 0 = 24 h [C].

## 4. Contradictions found (recorded, not resolved)
1. `createBond` present in app code: **resolved 2026-10-13** (REVIEW-PHASE1). Smali evidence accepted; FACTS §2 row retired. Trigger conditions of two sites go to C900-Q14.
2. `client/c900/frames.py`: `FIXED_BYTE` comment incomplete (version byte) and SimWatch ack x = `00 01` unsourced [I]. Client not edited (Phase 3).

## 5. Still needed
| Item | Settles it |
|---|---|
| Q14 step 1 remainder (now C900-Q16): cmd 5 field maps in StepUtils, HrUtils, DevBaseDataUtils, SleepUtils, TempUtils | static (DRAFT); the rest of Q14 is done |
| C900 adv name, services, bonding (Q01-Q03) | owner HCI snoop (Q13 -> Q19) first; HW-2/HW-3 only if needed |
| C900 `PROTOCOL_VERSION` (0x2A27), feature map bytes (0x2A28) incl. `binPreviewFlag`, contacts bit | HW-2 read-only 0x180A reads |
| Watch's own ack x value; which keys it acks | HW-4 single writes, or a capture |
| OTA 0x81 values (mtu, group, timeout) | capture or an approved OTA session only |

## Decisions from findings
| ID | Finding | Decision | Rationale |
|---|---|---|---|
| D-stop-b | createBond conflict with FACTS | Q05 partial; record conflict, pick no winner | OPEN-QUESTIONS stop condition (b) |
| D-bond | Reviewer: 3 named smali hits vs one negative jadx search; Q14 mapped the triggers | Retire "no createBond"; app bonds only on 0x0C/19, 0x0E/1, or cmd 2 key 1 ack + b15 0x40 [C]; device side [U] | A negative search is falsified by a reproducible positive hit (REVIEW-PHASE1) |
| D-nolive | Owner 2026-10-13: no live test until necessary | Phase 2 parked; HW-0 written as a doc only; static Phase 1b first | Owner instruction; software first |
| D-next | Remaining unknowns are mostly device-side | Next: Q16 + Q17 + Q18 static, then owner capture (Q13/Q19); HW-0 last. See NEXT-STEPS.md (DRAFT) | Software first; capture is the owner's own traffic, no new contact by us |
| D-version | Byte 4 follows 0x2A27 | HW-2 must read 0x2A27 before any write; codec must take the version as input in Phase 3 | A hard-coded 01 could be wrong on some firmware |
| D-interval | OTA interval unused | Do not copy any interval into a future design; pacing = write-complete | Copying 300/500 would be cargo cult |
| D-secrets | Signing key literal in app | Not recorded anywhere | AGENTS.md; no benefit |
| D-client | Codec comment/ack inaccuracies | Leave client untouched; list for Phase 3 | Phase 1 is static docs only |

## Phase 1b (approved 2026-10-13)
- **C900-Q14 (static):** steps 2-7 done [C]; step 1 partial (cmd 5 key map and inline SpO2; five parser classes left, stop rule). Main result: the app calls createBond only on a watch-side signal (two inbound messages or one feature bit; the third path is app-initiated after the time-sync ack, gated by the watch's b15 0x40). The prompts are inbound 0x0C/19, inbound 0x0E/1 (classic MAC, up to 3 tries 35 s apart), or an ack of cmd 2 key 1 in sync with feature b15 0x40 (target MAC is the BLE MAC with its last byte XOR 0x55). Shutter = 0x0C key 2. Battery byte 0 = percent, then bind 500 ms later. Feature b25 0x80 is shared by HR auto test and DND. Details: `tasks/results/C900-Q14.md`.
- **C900-Q15:** `tasks/HW-0-RUNSHEET.md`, DRAFT, zero writes, not run. HW-3 uses a single-UUID listener because `tools/notify_log.py` would subscribe to OTA characteristics.
- **Owner guide:** `docs/guides/HCI-CAPTURE-ANDROID.md`; `captures/` is git-ignored.
- **Next:** owner decides on an optional HW-1 capture; HW-0 needs a separate approval before anything runs.
