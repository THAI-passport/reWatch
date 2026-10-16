# R09: Consolidate live evidence into proposed doc diffs

Kind: docs (proposals only). Time box: 1.5 h. You own: `results/R09.md`.

## Inputs
`tasks/results/LIVE-SESSION-1-2026-10-13.md`, `LIVE-SESSION-2-2026-10-13.md`, `LIVE-SESSION-3-2026-10-13.md`, `C900-Q19.md` (incl. sections 6-8), `S-21-S-22.md`, `OWNER-QR-2026-10-13.md`; FACTS, PROTOCOL, INVARIANTS, OPEN-QUESTIONS.

## Steps
1. Table every `[H]` claim: claim, source file and section, current tag in FACTS/PROTOCOL/INVARIANTS, proposed tag.
2. Flag overclaims, for example: "zero link keys created" (macOS cannot report bonds), multiple `time` runs where the sheet said no retries, "bind not needed" generalised beyond the commands tested, message ack never received (probe stopped on 0x0E/1).
3. Write exact proposed text for: a new PROTOCOL section "Hardware-confirmed behaviour (2026-10-13)", FACTS rows to add or retag, OPEN-QUESTIONS Q01-Q03 status lines.

## Done when
Every live result is mapped; overclaims listed with a corrected wording.
