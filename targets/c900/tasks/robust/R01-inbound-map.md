# R01: Inbound command map vs what the core handles

Kind: static. Time box: 2 h. You own: `results/R01.md`.

## Why
`Session.onCommand` acks every inbound DF frame and flags only the two bond triggers. Live session 3 showed the watch sends unsolicited `0x0E key 1` in a normal session [H]. We need every frame the watch can send and what the vendor app does with it.

## Inputs
PROTOCOL 7, 7.1, 7.2; `tasks/results/C900-Q05.md`, `C900-Q14.md`; `client/c900-android/core/src/main/kotlin/rewatch/c900/Session.kt`.

## Steps
1. `dexgrep.py $APK methods 'NotifyWriteUtils'`, then `dump 'NotifyWriteUtils;' dataHandle`. Map each cmd branch (switch / if-eq on frame index 4) to its handler.
2. For each handler record per (cmd, key): app action (UI only / reply frame / storage / createBond / timer / disconnect).
3. Record when the app sends its FD ack (before/after handling, skipped for which cmds).
4. List rows missing from PROTOCOL 7.x.
5. Compare with `Session.kt` behaviour today.

## Output
| cmd | key | meaning | app action | app replies with | core today | proposed core behaviour | tag/evidence |

## Stop conditions
Hash mismatch: stop. A handler unreadable in 20 min: mark `[U]` with class->method, move on.

## Done when
Every cmd in `dataHandle` has a row; proposed core behaviour written for 0x0E/1, 0x0C/19, 0x0C/8, 0x0C/9, 0x19.
