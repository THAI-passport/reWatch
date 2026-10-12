# C900 / Hiwear Plus: invariants and quirks (read before editing any c900 doc or code)

These are facts that were wrong at least once, or are easy to "simplify" away. Each row says what is true, what the tempting wrong version is, and where the proof lives. **Do not change, drop or soften a row without new evidence of equal or higher tag** (smali over jadx, `[H]` over `[C]` for device behaviour), and record the change in FACTS.md and docs/steps.md in the same commit. `tests/test_c900_invariants.py` checks that the machine-checkable ones still hold.

Rule for agents: before you finish a pass, grep your diff for each "Wrong version" below. If your text says it, you are wrong or you need a FACTS row.

## Identity
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-01 | Companion app is Hiwear Plus `com.myled.HiwearPlus` 2.0.1/31 | HryFine / HiWatch Pro is the app | [owner]+[C] pin | FACTS §1, SOURCES.md |
| I-02 | Stack is Bluetrum (abpartool, 0x18A8); no Jieli | Use Jieli RCSP / `re-jieli` playbook | [C] | PROTOCOL §1 |

## Frame and link
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-10 | Byte 4 is `PROTOCOL_VERSION` (default 1, overwritten from 0x2A27 major) | byte 4 is a fixed `01` | [C smali] | C900-Q04; `IssuedUtil.getSendByte` |
| I-11 | len = payload + 5; total = len + 4 | len = payload + 6 (Gemini) | [C]/[V] | PROTOCOL §4; vector `df0005ee0901000000` |
| I-12 | Sum = all bytes mod 256 with byte 3 taken as 0 | sum excludes header / is a CRC | [C]/[V] | PROTOCOL §4 |
| I-13 | Command service ends `...DCCA9F`; the OTA one ends `...DCCA9E` | they are the same service | [C] | PROTOCOL §2 |
| I-14 | 0xFF00 and 0x18A8 are OTA/DFU, never command | 0xFF00 is the command service, MTU 512 (Gemini) | [C] | FACTS §2 |
| I-15 | One command in flight; 100 s ack timeout (`0x186a0`) | fire-and-forget, short timeout | [C smali] | C900-Q04 |
| I-16 | Retries: full 20-byte pieces 2x100 ms; last piece 1x20 ms; frames <=20 B none | two retries on every piece | [C smali] | C900-Q04 |
| I-17 | App NAK on bad sum: x = 3, status 0; ACK x = 0, status 1 | app acks always x = 0 | [C smali] | C900-Q04 |
| I-18 | Watch ack bytes 6-7 are unknown; SimWatch `00 01` is a guess | SimWatch ack is real | [I] | FACTS §4 |

## Commands
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-20 | Blocked forever: 0x01 OTA, 0x04 UNBIND, 0x06 RESET, 0x07 FACTORY_TEST, 0x0D RESTORE, 0x13 OTA_NEW | 0x04 = watch-face prep, 0x07 = find device (Gemini) | [C] | CommandID; `frames.BLOCKED_CMDS` |
| I-21 | Time sync = cmd 2 key 1, year stored as year - 2000 (`-0x7d0`) | cmd 0x0A, or full year | [C smali] | results/S2 |
| I-22 | cmd 2 key 26 payload 1 = 12 h, 0 = 24 h | 1 = 24 h | [C] | C900-Q05 |
| I-23 | cmd 0x1A key 21 = exit find-phone | language (jadx label) | [C smali] | C900-Q04 |
| I-24 | jadx substitutes same-valued library constants (CHATGPT_ID, GET_FUNTION, CropImageView 500, FileUriModel "/", JCameraView.MEDIA_QUALITY_FUNNY = 400000) | trust jadx names for numbers | [C] | C900-Q04, Q06, Q07 |
| I-25 | Negative claims ("app never calls X") need a smali search | jadx search found nothing, so [C] | lesson | LOG.md 2026-10-13; docs/SOP.md |

## Bonding, features, inbound
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-30 | App calls createBond only on: inbound 0x0C/19; inbound 0x0E/1 (3 tries, 35 s); ack of cmd 2 key 1 in sync with feature b15 0x40 (MAC last byte ^ 0x55) | "app never bonds" or "app always bonds" | [C smali] | C900-Q14; FACTS §4 |
| I-31 | Whether the C900 itself asks to bond is unknown | it does / it does not | [U] | Q03 |
| I-32 | Feature map byte 0 must be 0xAA; arrives by 0x2A28 read and cmd 0x19 | any byte 0 is fine | [C] | C900-Q05 |
| I-33 | Feature b25 0x80 hides both HR auto test and DND | jadx duplicate typo | [C smali] | C900-Q14 step 7 |
| I-34 | `HexUtil.byte2IntLR` is big-endian over argument order | little-endian ("LR") | [C] | C900-Q06 |
| I-36 | Health records use a 2-byte date: year-2000 = (b0&0x7F)>>1, month = (b0&1)<<3 \| b1>>5, day = b1&0x1F; payload integers are big-endian | reuse the cmd 2 key 1 time packing, or little-endian | [C smali] | C900-Q16 |
| I-35 | Connect order: 0x2A27 -> 0x2A26 -> features -> battery -> (500 ms) bind cmd 3 key 0 | bind first | [C] | C900-Q14 step 6 |

## OTA, faces, contacts (document only, never implement without Phase 4 approval)
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-40 | Store faces, DIY faces, wallpapers and contacts all go over the OTA path (D5/D6 on 0xFF00) | there is a DF opcode for faces or contacts | [C] | PROTOCOL §6; C900-Q08 |
| I-41 | OTA `sendInterval` (500 init / 300 substitute) is never used; pacing = write-complete + 10 ms | send every 300 or 500 ms | [C smali] | C900-Q07 |
| I-42 | Dial trim applies to store faces only, and only when `binPreviewFlag` (b18 0x20) allows | trim every dial | [C smali] | C900-Q06 |

## Process and safety
| ID | True | Wrong version | Tag | Proof |
|---|---|---|---|---|
| I-50 | `tools/notify_log.py` always applies an OTA/DFU deny list (0xFF00, 0x18A8, their chars, `...dcca9e`); `--only` with a denied UUID exits 2. Before C900-Q17 it subscribed to everything | it is passive, so any version is safe; or `--only` turns the deny list off | [C] tool code + tests | C900-Q17; `tests/test_notify_log.py` |
| I-51 | No live test until the owner says it is necessary; capture before HW-0 | probe the watch to check a doc | owner rule | NEXT-STEPS.md |
| I-52 | Only the Gemini doc's frame layout is kept; its opcodes are wrong | Gemini opcodes as a fallback | [C] | FACTS §2 |
| I-53 | Nothing becomes `[H]` without a capture or hardware result file | simulator/test agreement = confirmed | AGENTS rule 6 | AGENTS.md |
