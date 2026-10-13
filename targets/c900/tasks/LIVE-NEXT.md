# Next pass for the agent on the owner's machine (2026-10-13)

Branch: `claude/lucid-galileo-1dma0d` (contains the integrated robustness pack). Read first: `AGENTS.md`, `targets/c900/tasks/AGENT-BRIEF.md`, `targets/c900/LOG.md` section "Robustness pack integration", skill `re-privacy-scrub`.

Ground rules for this pass: no new radio session unless the owner approves it in this chat for task 3; no writes beyond the probe allowlist; never copy the capture or probe logs into git or to a cloud session; stop at the first unexpected watch response.

## Task 1 (no radio, AI alone): run the Kotlin tests
```bash
git fetch origin claude/lucid-galileo-1dma0d && git checkout claude/lucid-galileo-1dma0d
cd client/c900-android && ~/tools/gradle/bin/gradle :core:test
```
Expected: BUILD SUCCESSFUL, all tests in `CoreTest` and `FuzzTest` pass. If a test fails: do not edit the test to pass; paste the failure (test name, assertion line) into `targets/c900/LOG.md` and stop task 1. If it is a compile error in `Session.kt`, `CommandQueue.kt` or `Frames.kt`, fix only the compile error, rerun, and record it.

## Task 2 (no radio, AI + owner screenshot): settle distance and calorie units [U]
1. From the existing capture `captures/btsnoop_hci.log.last` (owner machine only), decode every inbound cmd 5 key 2 and key 12 frame with `python3 tools/btcap.py` (see skill `re-capture-ingestion`). Note raw distance and calorie integers per frame. Do not save payloads anywhere tracked.
2. Ask the owner for one screenshot (or typed numbers) from the Hiwear Plus app for the same day: steps, distance, calories as displayed, and the unit setting (km/mi).
3. Compare: if displayed km x 1000 == raw distance (within rounding), distance is meters `[H]`; same test for kcal vs raw calorie. Anything else: record both numbers and leave `[U]`.
4. Write the result in `targets/c900/FACTS.md` (replace the `[U]` row under "Robustness pack") and one line in `LOG.md`. Only counts, never message text or account data.

## Task 3 (radio, needs owner approval first): none planned
No live write is needed for this pass. If the owner wants one, the only candidate is a read-only `inspect --listen 60` to see whether 0x0E key 1 also arrives with no message push. Budget: 1 connect, 0 writes. Command:
`.venv-probe/bin/python tools/c900_probe.py inspect --name "Watch Ultra" --listen 60`

## Decision to ask the owner (do not decide yourself)
The watch sends cmd 0x0E key 1 after a message push, and the core turns that into a bond prompt every time. Options: (a) keep prompting, (b) prompt once per session, (c) never prompt, cache the classic MAC only. Record the answer in `targets/c900/CLIENT-DESIGN.md`.

## When done
Commit `c900 G4: <what>` on the same branch, push, and report: test result, unit result with tag, owner's decision.

## Update after the follow-up static pass (same day)
- Units are now [C] from the app's display code (FACTS "Robustness pack"). Task 2 is still wanted: it turns them into [H]. If the owner numbers disagree with raw / 1000, record both and flag it in LOG.md; do not edit the [C] row.
- Task 1 now also covers the new `HealthSyncTest` and the privacy-scan change: run `python3 -m unittest discover -s tests` too (expected OK).

## Completed on owner machine (2026-10-14)
- Task 1: 26 Kotlin tests (`CoreTest`, `FuzzTest`, `HealthSyncTest`) and 150 Python tests passed locally.
- Task 2: Distance and calorie units settled [C] across Key 12 and Key 2 (`HistoryStepAdapter.getView`, `HomeFragment`).
- Decision: Owner chose option (c) (never prompt on 0x0E key 1, silent cache for automatic/sleep operation). Recorded in `CLIENT-DESIGN.md`.
