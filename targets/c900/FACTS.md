# Fact sheet: C900 watch

Single place for values that sources disagree on. Other documents link here. Change a value here first.

Tags: [C] confirmed in artifact, [V] verified by emulation/vector, [H] hardware, [W] third-party, [I] inferred, [U] unknown.

| Topic | Value | Tag | Source | Conflicts with |
|---|---|---|---|---|
| Ack header byte | 0xFD | [W] | landscape doc 3.2 | app frames start 0xDF; the doc may have swapped or mistyped one; settle in code (G2) |
| Length field meaning | total = Len + 4 | [W] | landscape doc 3.2 | header is 4 bytes before Cmd, so Len likely counts Cmd onward [I]; settle with a worked example from code |
