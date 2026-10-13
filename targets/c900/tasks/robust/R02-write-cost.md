# R02: How often the app writes each command (write cost, rate limits)

Kind: static. Time box: 2 h. You own: `results/R02.md`.

## Why
Ground rule 7: before the client sends anything often, learn the rate the vendor app uses; that is the only rate the firmware is known to survive. The core's 200-writes-per-session budget is a placeholder.

## Steps
1. `dexgrep.py $APK methods 'SettingIssuedUtils'`; for each builder, `refs` its name to find callers and the trigger (connect, user action, timer, broadcast such as time-zone change, notification arrival).
2. Message push (cmd 2 key 18): de-dup, rate limit, queue length.
3. Time sync: how often per connection; on time/time-zone change?
4. Any guard that skips a write when the value is unchanged.
Read timer values from bytecode `const`, not jadx names (I-24).

## Output
| Command (cmd/key) | Trigger(s) | Max rate in code | De-dup/throttle | Tag/evidence |
Then "Proposed client limits" with the evidence behind each number.

## Done when
Rows for time, message, find, 12/24 h, step goal, alarms; limits proposed.
