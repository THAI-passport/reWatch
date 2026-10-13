# R03: Transport (connect, reconnect, MTU, timers, bond retries)

Kind: static. Time box: 2.5 h. You own: `results/R03.md`.

## Why
The app shell needs exact transport parameters. Known: MTU 32, 20-byte pieces 20 ms apart, I-16 retries, 100 s ack timeout, failed write disconnects. Unknown: reconnect policy, scan settings, disconnect cleanup, and how the 0x0E/1 bond attempt (I-30: 3 tries, 35 s) interacts with the LE link.

## Steps
1. `methods 'MBleManager'`; dump `connect` and the BLESSED callbacks (connected, disconnected, connection failed, MTU changed, services discovered) and anything scheduling reconnects.
2. Record autoConnect, reconnect delays and attempt cap, scan mode/filters, MTU request and timing, connection priority, notify-enable order, every timeout literal.
3. Disconnect path: what is cleared, what is retried.
4. Bond: dump the `MainActivity$4` runnable and the createBond sites (I-30). Does the LE session pause during bonding? Any bond removal?
5. Any `getBondState()` check gating commands.
Do not study OTA classes beyond noting they pause the command channel.

## Output
Answers table, then "Transport parameters" as named constants with values and tags.

## Done when
Reconnect, MTU, timers, cleanup and bond retry each have evidence or `[U]` with what was tried.
