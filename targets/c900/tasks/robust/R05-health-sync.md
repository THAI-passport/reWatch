# R05: Health and fitness data synchronization (cmd 0x05)

Kind: static. Time box: 2 h. You own: `results/R05.md`.

## Why
The Kotlin client core needs to support pulling activity and health records (steps, sleep, heart rate, temperature) into local storage as outlined in `CLIENT-DESIGN.md` section 2. We know the payload field maps for keys 2, 4, 5, 9, 12, 14 from `C900-Q16.md`, but the sync handshake sequence (request trigger, start/end markers, ack requirements, timeout) and remaining field maps (key 13 temperature, key 15 sport modes, units of distance/calories) remain unresolved.

## Inputs
`targets/c900/PROTOCOL.md` section 7, 7.2; `tasks/results/C900-Q05.md`, `C900-Q14.md`, `C900-Q16.md`; `INVARIANTS.md` I-34, I-36; `client/c900-android/core`.

## Steps
1. Sync state machine: Inspect `HealthUtils.sportAckSuccess` and callers. Map the sync initiation sequence: how does the app trigger sync (cmd 5 key 1 vs cmd 5 key 6 real-time steps)? How are start (key 7) and end (key 8) markers handled?
2. Ack and pacing: Does the app send FD acknowledgments for incoming DF cmd 5 frames, or only specific keys? Check idle timeout (5 s timer in Q05) and retry behavior.
3. Remaining field maps:
   - Key 13 (`TempUtils.getTempDataList`): stride, date format, temperature scaling / units.
   - Key 15 (`DevBaseDataUtils.getSportModeData`): sport types, duration, calories, metric layout.
   - Units verification: Resolve units for distance and calories in Key 2 (`StepUtils.getSportBy1Hour`) and Key 12 (`StepUtils.getTotalStepData`).
4. Core behaviour proposal: Define state machine transitions and storage payload schema for the open client core without cloud/server dependencies.

## Output
- Answers table: (question, answer, tag, evidence)
- Sync sequence table: (trigger -> transmission -> ack -> completion)
- Field map table for keys 13 and 15
- Proposed Kotlin client core interface and events for activity sync

## Stop conditions
Hash mismatch: stop. If a parser method is unreadable or obfuscated within 20 min, mark `[U]` with class->method and move to next step.

## Done when
Sync trigger and termination sequence documented with citations; keys 13 and 15 mapped or tagged `[U]`; proposed client sync flow defined.
