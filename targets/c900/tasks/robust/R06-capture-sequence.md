# R06: Capture sequence fixture (no payloads)

Kind: capture. Runs only on the owner's machine where `captures/btsnoop_hci.log.last` exists. Time box: 1.5 h. You own: `results/R06.md`, `tests/fixtures/c900_q19_sequence.json`.

## Why
The Kotlin simulator should replay the real order and timing of the vendor app session, without any personal bytes.

## Steps
1. `python3 tools/c900_decode.py captures/btsnoop_hci.log.last --json captures/r06.json` (if `--json` is missing, use the decoder's Python API as C900-Q19 did; keep everything under `captures/`).
2. Build the fixture: a list of `{"t": seconds_from_first_frame (3 decimals), "dir": "tx"|"rx", "type": "df"|"fd", "cmd", "key", "ver", "plen", "x", "status"}`. **No payload bytes, no addresses, no handles.**
3. Add a header object: source "C900-Q19 capture", frame counts, decoder version (git commit).
4. In R06.md: ack latency stats per cmd (min/median/max), gaps, every 0x0E/1 time, anything not in PROTOCOL 7.

## Stop conditions
Capture missing: stop, write "not run". Any field you cannot reduce to the list above: drop it.

## Done when
Fixture validates (`python3 -c "import json;json.load(open('tests/fixtures/c900_q19_sequence.json'))"`), privacy scan clean, R06.md written.
