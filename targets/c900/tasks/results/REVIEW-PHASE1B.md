# REVIEW-PHASE1B result

Date: 2026-10-13 (Asia/Saigon). Docs only. No bootstrap (no check needed code), no watch, no app, no server. One local smoke test: `python3 tools/btcap.py tests/fixtures/synthetic_gatt.btsnoop` runs and prints raw ATT hex (no DF decoding). `tshark` is not installed in this container.

## Part A: revisions
| Item | Finding | Change |
|---|---|---|
| Q14 claims | Steps 2-7 cite class + smali literal; step 2 tag lengths for 4/7/9/11 honestly marked [C jadx]; step 3 is jadx-only and tagged so; the paper size for resolution 2 is a "library constant [U]" | No tag changes needed. No new [C] added. |
| Bonding | PROTOCOL said "never unprompted", but path 2 is app-initiated after the time ack, gated by a watch feature bit | Wording aligned in PROTOCOL §3, recon-v2 Phase 1b and D-bond: three watch-side gates (0x0C/19, 0x0E/1, time ack + b15 0x40). FACTS §4 already exact. |
| Q14 step 1 | Partial | Rewritten as standalone C900-Q16 with acceptance (offset, width, endianness, unit, synthetic example per key). |
| HW-0 run sheet | Zero writes OK; abort triggers present | Added: owner phone Bluetooth off (watch takes one central); never unbind to free the watch; no pairing agent on Linux / Cancel on macOS; macOS UUID instead of MAC; descriptor-write count explicit (1 CCCD); scan step no longer claims "manufacturer data" (app matches the raw scan record, bleak cannot show it; name [U]); checksum ref fixed to PROTOCOL §4; tool-hazard section pointing to Q17. |
| notify_log.py | Subscribes to every notifiable char (`main_async`) incl. OTA | DRAFT task C900-Q17 (`--only`, default deny list, refuse-to-start, tests). Tool not edited. |
| Capture guide | Accurate in outline | Added: send only btsnoop, not the bug-report zip (account, Wi-Fi, location data); profile and location may be sent during sync; do not open Contacts; do not unbind to re-bind (first bind also clears data and calls the server); Filtered mode cuts payloads; brand notes marked [W]; Huawei/Honor line. |
| Stale lines | PLAN header (Phase 1 only, author line), PLAN §6 "Proposed Phase 1", PLAN §7 Phase 0 stop rule, TARGET G3 "await Phase 0", recon-v2 "Phase 1b (DRAFT)" row, STATUS Q14 | Updated. |

## Part B: plan
`targets/c900/NEXT-STEPS.md` (DRAFT): four paths compared, order Q17+Q18 -> Q16 -> owner capture (Q13 -> Q19) -> HW-0 only for what is left; capture decision tree; Phase 3 entry criteria. New DRAFT tasks C900-Q16..Q19 and an owner Phase 1c checklist in OPEN-QUESTIONS.md.

## STOP
Nothing executed beyond docs. Awaiting owner sign-off on Phase 1c.
