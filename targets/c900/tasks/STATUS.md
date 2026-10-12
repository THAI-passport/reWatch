# Task status: C900 watch (Hiwear Plus)

States: `todo`, `doing`, `done`, `blocked: needs human`, `blocked: needs hardware`, `blocked: needs approval`, `skipped: not applicable`.

## Software (AI alone)
| Task | Title | State | Result |
|---|---|---|---|
| S0 | Baseline: tools, tests, lint | done | unittest and lint green 2026-10-13 |
| S1 | Acquire and decompile Hiwear Plus 2.0.1 | done | SOURCES.md, BUILD-INFO.txt (local) |
| S2 | Audit claims in PROTOCOL.md (smali for the time offset, frame vectors) | todo | |
| S3 | Server API inventory (static) | done (first pass) | PROTOCOL.md 8 |
| S4 | Firmware and watch-face transfer path (read only, never used) | todo | |
| S5 | Inbound message inventory | doing | PROTOCOL.md 7 |
| S6 | Scan filter audit vs client | done (app side) | PROTOCOL.md 3; client has no scanner yet |
| S7 | Fix client/c900 opcodes to the [C] table, with tests | todo | |
| S8 | Simulator assumption register | todo | |
| S9 | First-contact readiness | todo | |

## Hardware (prepared, not run; owner approval per session)
| Task | Title | State |
|---|---|---|
| HW-0 | Run sheet, approvals, write budget | todo |
| HW-1 | Optional reference capture with Hiwear Plus (owner's phone, HCI snoop) | blocked: needs approval |
| HW-2 | Read-only scan: name, scan record (MAC + 12 34?), services, 0x180A reads, battery | blocked: needs approval |
| HW-3 | Read-only notification listen after connect (no writes) | blocked: needs approval |
| HW-4 | First write: time sync (cmd 2 key 1), one frame | blocked: needs approval |
| HW-5 | Message push (cmd 2 key 18), one frame | blocked: needs approval |
| HW-6 | Find watch on/off (cmd 2 key 11) | blocked: needs approval |
| HW-7+ | Watch faces: not before a reviewed design | blocked: needs approval |
