# REVIEW-PHASE1 result

Date: 2026-10-13 (Asia/Saigon). Docs-only review of Phase 1 (C900-Q04..Q09). No bootstrap (decompiled tree absent; no check truly needed code), no watch, no app, no server.

## Per-result critique
| Result | Verdict | Notes |
|---|---|---|
| Q04 | sound | Literals smali-cited (`0x186a0`, `0x14`/`0x64`, keys `0x1a`/`0x1b`/`0x15`). Remaining `[U]` listed. The "most watches report major 1" is correctly `[I]`. |
| Q05 | sound, partial | Stop under rule (b) was correct. One self-contradictory cell (0x14 byte order "not yet checked" and "resolved" in the same cell) fixed. b25 duplicate bit is jadx only; carried to Q14. |
| Q06 | sound | Header-table reading correctly `[I]`; seeds `[V]`. |
| Q07 | sound | 300/500 explained with smali offsets and "no callers"; the no-callers claim is a negative search, so it holds only for this build. |
| Q08 | sound | Device-side contacts bit `[U]` until HW-2. |
| Q09 | sound | Signing key correctly not recorded. |

No new `[C]` claims were added by this review.

## Bonding decision
The old row ("no createBond in app code") was a negative search result on jadx output. Phase 1 gives three named, reproducible smali call sites. A reproducible positive hit falsifies a negative search, so the old row is **retired** (FACTS §2 and §4, PROTOCOL §3). App side: the app calls createBond conditionally [C]. Open parts: the trigger conditions of the `setSettingSuccess` and `MainActivity$4.run` sites (C900-Q14), and whether the C900 ever asks (C900-Q03, hardware or capture). Re-check command for anyone with the tree: `rg -n "BluetoothDevice;->createBond" targets/c900/work/smali | grep -v welie` should print 3 lines.

## Other changes
- OPEN-QUESTIONS: Q04, Q06-Q09 closed; Q05 closed partial; new DRAFT C900-Q14 (inbound remainder, standalone) and C900-Q15 (HW-0 run sheet as a document, zero writes); Phase 1b checklist.
- PLAN: stale "Q09/Q12 parked" line corrected; Phase 1b section; Phase 2 parked per owner ("no live test until necessary").
- recon-v2: conflict marked resolved; decisions D-bond, D-nolive.
- STATUS: Q05/Q14/Q15/HW-0 rows aligned.

## Proposed next phase (DRAFT, needs owner sign-off)
Phase 1b, static only: C900-Q14 then C900-Q15. Hardware (Q01-Q03, HW-1..3) parked until you say it is necessary; Q13 owner capture stays optional.

## STOP
Review complete; Phase 1b not started.
