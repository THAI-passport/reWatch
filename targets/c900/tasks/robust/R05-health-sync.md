# R05: Health and fitness data synchronization (cmd 0x05)

Kind: static. Time box: 2 h. You own: `results/R05.md`.

## Why
The Kotlin client core needs to support pulling activity and health records (steps, sleep, heart rate, temperature) into local storage as outlined in `CLIENT-DESIGN.md` section 2. Field maps for keys 2, 4, 5, 9, 12, 13, 14 and 15 are already done in `C900-Q16.md` [C smali]; do not redo them. Still open: the sync handshake (request trigger, start/end markers, ack requirements, timeout) and the residual `[U]` items listed under "Still [U]" in C900-Q16.

## Inputs
`targets/c900/PROTOCOL.md` section 7, 7.2; `tasks/results/C900-Q05.md`, `C900-Q14.md`, `C900-Q16.md`; `INVARIANTS.md` I-34, I-36; `client/c900-android/core`.

## Steps
1. Sync state machine: Inspect `HealthUtils.sportAckSuccess` and callers. Map the sync initiation sequence: how does the app trigger sync (cmd 5 key 1 vs cmd 5 key 6 real-time steps)? How are start (key 7) and end (key 8) markers handled?
2. Ack and pacing: Does the app send FD acknowledgments for incoming DF cmd 5 frames, or only specific keys? Check idle timeout (5 s timer in Q05) and retry behavior.
3. Residual `[U]` from C900-Q16 (read where the parsed values are displayed or stored, since the parsers carry no units):
   - Distance and calorie units for key 2 (`StepUtils.getSportBy1Hour`) and key 12 (`StepUtils.getTotalStepData`): follow the bean fields to the UI formatting code (look for divisors such as 1000 or 100 and unit strings).
   - Meaning of the `type` byte in key 4 (HR) and key 13 (temperature) records.
   - modeData1-3 per sport mode in key 15 (`DevBaseDataUtils.getSportModeData`).
   - Whether `p[2]` of list headers and the unread record bytes are used anywhere else (`refs`).
   If a step contradicts a C900-Q16 offset, put it in Conflicts; do not silently change the map.
4. Core behaviour proposal: Define state machine transitions and storage payload schema for the open client core without cloud/server dependencies.

## Output
- Answers table: (question, answer, tag, evidence)
- Sync sequence table: (trigger -> transmission -> ack -> completion)
- Residual `[U]` table: (item, answer or still `[U]`, tag, evidence)
- Proposed Kotlin client core interface and events for activity sync

## Stop conditions
Hash mismatch: stop. If a parser method is unreadable or obfuscated within 20 min, mark `[U]` with class->method and move to next step.

## Done when
Sync trigger and termination sequence documented with citations; each C900-Q16 residual `[U]` answered or kept `[U]` with what was tried; proposed client sync flow defined.
