# Task status: C900 watch (Hiwear Plus)

States: `todo`, `doing`, `done`, `blocked: needs human`, `blocked: needs hardware`, `blocked: needs approval`, `skipped: not applicable`.

## Software (AI alone)
| Task | Title | State | Result |
|---|---|---|---|
| S0 | Baseline: tools, tests, lint | done | unittest and lint green 2026-10-13 |
| S1 | Acquire and decompile Hiwear Plus 2.0.1 | done | SOURCES.md, BUILD-INFO.txt (local) |
| S2 | Audit claims in PROTOCOL.md (smali for the time offset, frame vectors) | done | results/S2.md |
| S3 | Server API inventory (static) | done (first pass) | PROTOCOL.md 8 |
| S4 | Firmware and watch-face transfer path (read only, never used) | done (static) | results/S4.md; PROTOCOL.md 6 |
| S5 | Inbound message inventory | done (first pass) | results/S5.md; PROTOCOL.md 7 |
| S6 | Scan filter audit vs client | done (app side) | PROTOCOL.md 3; client has no scanner yet |
| S7 | Fix client/c900 opcodes to the [C] table, with tests | done | results/S7.md; client/c900/frames.py |
| S8 | Simulator assumption register | done (first pass) | results/S8.md |
| S9 | First-contact readiness | done (checklist) | results/S9.md |
| RECON-HIWEAR-APK | Phase 0 plan review, then Phase 1 | Phase 0 signed off; Phase 1 run 2026-10-13 (Q05 partial); reviewed 2026-10-13 (results/REVIEW-PHASE1.md) | [recon-v2.md](../recon-v2.md); [RECON-HIWEAR-APK.md](RECON-HIWEAR-APK.md); start [recon-v1.md](../recon-v1.md); drafts [PLAN.md](../PLAN.md), [OPEN-QUESTIONS.md](../OPEN-QUESTIONS.md) |

**Note:** Further `client/c900` feature work is **deferred** (PLAN.md Phase 3). S7 codec sketch remains; do not expand until owner approves.

## Open questions (from OPEN-QUESTIONS.md)

Phase 0 signed off 2026-10-13; Phase 1 static pass run the same day. Start brief: [recon-v2.md](../recon-v2.md) (then recon-v1).

| ID | Title | Priority | Gate | State | Result |
|---|---|---|---|---|---|
| C900-Q01 | Adv name / scan marker | P0 | hardware-approval | blocked: needs approval | |
| C900-Q02 | GATT services on device | P0 | hardware-approval | blocked: needs approval | |
| C900-Q03 | Bonding behaviour | P0 | hardware-approval | blocked: needs approval | |
| C900-Q04 | Cmd key/payload tables | P1 | static | done (tasks/results/C900-Q04.md) | |
| C900-Q05 | Inbound DF map | P1 | static | done (partial); conflict resolved 2026-10-13; remainder -> C900-Q14 | tasks/results/C900-Q05.md |
| C900-Q06 | Dial.bin decode/trim | P1 | static | done (tasks/results/C900-Q06.md) | |
| C900-Q07 | OTA 0x81 / CRC docs | P1 | static | done (tasks/results/C900-Q07.md) | |
| C900-Q08 | Contacts = OTA main 4 | P1 | static | done (tasks/results/C900-Q08.md) | |
| C900-Q09 | Server inventory expand | P2 | static | done (tasks/results/C900-Q09.md) | |
| C900-Q10 | HryFine compare | P2 | static | skipped: needs pin | |
| C900-Q11 | PAR native layout | P2 | static | deferred | |
| C900-Q12 | Cus5610 inventory | P2 | static | parked (OTA/DFU risk, not needed now) | |
| C900-Q14 | Inbound map remainder + createBond conditions | P1 | static | blocked: needs Phase 1b sign-off (DRAFT) | |
| C900-Q15 | HW-0 run sheet (document only) | P1 | static | blocked: needs Phase 1b sign-off (DRAFT) | |
| C900-Q13 | Existing owner capture (HW-1) | P0 | owner supplies, then static | No capture yet (2026-10-13); optional owner-run Android HCI snoop before HW-0 | |
| C900-D01–D07 | Client/impl items | Deferred | — | deferred | PLAN.md Phase 3–4 |

## Hardware (prepared, not run; owner approval per session)
| Task | Title | State |
|---|---|---|
| HW-0 (= C900-Q15) | Run sheet, approvals, write budget (document only; owner: no live test until necessary) | blocked: needs Phase 1b sign-off |
| HW-1 (= C900-Q13) | Optional reference capture with Hiwear Plus (owner's phone, HCI snoop) | blocked: needs approval |
| HW-2 (= C900-Q01, Q02) | Read-only scan: name, scan record (MAC + 12 34?), services, 0x180A reads, battery | blocked: needs approval |
| HW-3 (= C900-Q03; uses Q05 map) | Read-only notification listen after connect (no writes) | blocked: needs approval |
| HW-4 | First write: time sync (cmd 2 key 1), one frame | blocked: needs approval |
| HW-5 | Message push (cmd 2 key 18), one frame | blocked: needs approval |
| HW-6 | Find watch on/off (cmd 2 key 11) | blocked: needs approval |
| HW-7+ | Watch faces: not before a reviewed design | blocked: needs approval |
