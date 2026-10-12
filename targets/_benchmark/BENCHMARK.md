# Benchmark (no research is recorded here)

This note only holds the prompt and the pass criteria. No T900 or C900 research has been done in this repo. Run the benchmark in a fork or on a branch; never commit vendor artifacts.

## Prompt
```
Reverse engineer: the T900 and C900 watch app.   Goal: scan, connect, read basic status and push a watch face or notification from a Python CLI.
```

## Seed material
`docs/recon/budget-smartwatch-landscape.md` (all `[W]`). It names a likely app per watch and a Nordic-UART frame layout for one of them; use it to seed hypotheses, not facts. Next-pass instructions: `docs/NEXT-PASS-PROMPT.md`.

## Pass criteria
- `targets/<slug>/` has SOURCES.md with hashes (pinned by version and SHA-256, not a floating link).
- PROTOCOL.md where every row is tagged.
- FACTS.md for disputed values.
- `client/<slug>/` with `pytest -q` green and a `--dry-run` mode.
- `python3 tools/rw.py lint` green.
- No vendor artifact tracked.
- HANDOFF.md listing hardware unknowns.
- Whether both models share one app or one protocol is a finding to record, not an assumption.
- Software first: no hardware step was taken without the owner's approval, and `docs/SOP.md` was updated after each pass.
