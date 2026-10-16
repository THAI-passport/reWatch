# IMPROVE-PLAN result (Phase 0 critique)

Date: 2026-10-12. Docs only; no code, no decompile, no bootstrap, no hardware.

## Changes
- recon-v1.md: `[owner]` tag defined as weighing like `[W]`; 100 s ack timeout flagged for smali check; OTA timing row added (from PROTOCOL §6.3); decisions D-order and D-capture added; review notes on weak tags and missing inbound table.
- OPEN-QUESTIONS.md: priority = importance, not run order; recommended run order; Who (AI vs human) rule; shared stop conditions; Q01 depends on HW-0 and Q13; Q04 starts with the timeout smali check and leaves unreached rows `[U]`; Q07 rescoped to smali verification (300 vs 500 interval conflict); new C900-Q13 (ask owner for an existing HCI capture); sign-off checklist extended.
- PLAN.md: run-order note (static Phase 1 before P0 hardware); three new risks; recommended Phase 1 set and budget.
- STATUS.md: Q09/Q12 moved from `todo` to blocked on sign-off (they were runnable before approval); Q13 row; HW rows cross-referenced to question IDs.
- RECON-HIWEAR-APK.md: typo.

## Contradictions found
- STATUS let Q09/Q12 run before Phase 0 sign-off while PLAN forbids it. Fixed.
- OTA send interval: default 300 ms vs field init 500 ms in PROTOCOL §6.3. Not resolved; assigned to Q07.
- No conflict with FACTS found.

## STOP
Phase 0 improve pass done. Waiting for owner sign-off; Phase 1 not started.
