# R08: Adversarial review of the Kotlin core

Kind: review (read only). Time box: 2 h. You own: `results/R08.md`.

## Scope
`client/c900-android/core/src/main/kotlin/rewatch/c900/*.kt` against: `docs/guides/PROBE-SECURITY.md`, `targets/c900/tasks/results/DEEP-PASS-1.md` (probe findings), INVARIANTS I-13..I-36, CLIENT-DESIGN section 4.

## Look for
Any path that builds a blocked or non-allowlisted command; any way a caller can choose a GATT target; ver handling gaps; ack matching errors (stale, wrong key, duplicate); timeout or budget bypass; unbounded memory; a hostile watch steering behaviour (floods, malformed lengths, fake acks, repeated bond triggers); bond without user consent; privacy (anything that could log message text, addresses, tokens); differences from the Python reference (`client/c900/frames.py`).

## Output
Findings table: severity (high/medium/low/note), file:line, failure story, proposed fix, test that would catch it. Then explicit non-findings.

## Done when
Every item above has a finding or a non-finding line.
