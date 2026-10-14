---
name: re-step-rationale
description: How to write the step and rationale entries in docs/steps.md, task results and handoffs so a later agent, with none of this session's context, can see why each choice was made, does not redo or undo it, and knows when to revisit it. Load when writing steps.md, a handoff, a task result, or before changing something that looks odd.
---

# re-step-rationale

AGENTS.md requires every step and decision in `docs/steps.md`. This skill is how to write them so they are useful later. The reader is an agent that cannot see this session: it has the repo, the docs, and nothing else.

## Before you act: read the decisions first
Before you "fix" a workaround, an odd constant, a skipped tool or a rejected claim:
1. `grep -n "<thing>" docs/steps.md targets/<slug>/LOG.md targets/<slug>/FACTS.md`
2. If an entry explains it, follow it, or supersede it with a new entry that says what changed (new evidence, new artifact version, the owner said so). Never undo a recorded decision silently.

## When to write an entry
| Situation | Entry? |
|---|---|
| Chose between two or more ways (tool, branch, design, wording) | yes |
| Rejected or downgraded someone's claim | yes, with what you checked |
| Worked around a platform or tool failure | yes, with the error |
| Stopped early (throttling, budget, stop rule) | yes, with what is left |
| Routine command with no alternative (ran the tests, ran lint) | no; put results in the commit or LOG.md |

One entry per decision, written when you make it (not at the end of the session from memory).

## Entry format
```
- **Step:** <action, command or file change, exact enough to repeat>
  **Decision:** <what was chosen>; rejected: <alternatives, or "none">
  **Rationale:** <the constraint or evidence that forced it, and the failure it avoids>
  **Evidence:** <tag + citation: [C] Class->method / smali constant, [H] log file, [V] test name>
  **Revisit if:** <the observation that would make this decision wrong>
```
Fields may share a line when short. Omit **Evidence** only when the step rests on no fact. **Revisit if** is required for design choices and placeholders; it turns a rationale into a test that someone can falsify later.

## Rules
- The rationale names a cause outside the decision itself: a constraint, an error, a measurement, a rule in AGENTS.md. "To find classes" is not a cause.
- Name what you checked, not what you believe. "Spot-checked with `dexgrep dump ... onDisConnected`: `const-wide/16 10000`" beats "verified".
- When you reject a claim, cite the check that failed ("class `FormatUtils` does not exist in the pinned APK"), so the next agent does not re-accept it.
- Placeholders (timeouts, budgets, caps chosen without evidence) are tagged `[I]` and say so in the entry and in a code comment next to the constant.
- Facts belong in FACTS.md and PROTOCOL.md; the entry links them. Do not restate values that may later change in two places.
- Append only. To change a decision, add a new entry that names the old one.
- No decompiled code, no personal data, no capture payloads.

## Handoffs and summaries
A summary of other agents' results is a copy and drifts. In a handoff, link each claim to the result file or doc row that holds it, and mark anything you did not re-check as "not re-checked". A reader who finds a mismatch trusts the result file, not the summary.

## Examples from c900
Bad:
- **Step:** ran dexgrep. **Rationale:** to find classes.

Good:
- **Step:** `dexgrep dump 'BaseReconnectBlueActivity;' onDisConnected`. **Decision:** dexgrep; rejected: jadx. **Rationale:** jadx cannot be installed in the cloud session and the question was one constant. **Evidence:** [C] `const-wide/16 10000`. **Revisit if:** a new APK version is pinned.
- **Step:** `HealthSync.IDLE_TIMEOUT_MS = 30000`. **Decision:** fixed placeholder; rejected: R05's 5 s "SPORT_DATA_TIME_OUT". **Rationale:** that constant does not exist in the APK; some value is needed so a stalled sync ends. **Evidence:** [I]. **Revisit if:** a full-sync capture shows gaps between records near or above 30 s.
- **Step:** kept the bond prompt on inbound 0x0E key 1. **Decision:** no change; rejected: R01's silent drop. **Rationale:** stopping a pairing prompt is a user-facing design choice for the owner (AGENTS.md "stop and ask"). **Revisit if:** the owner answers the question in LIVE-NEXT.md.

## Self-check before you stop
- [ ] Every non-routine choice this session has an entry.
- [ ] Every rejected or downgraded claim names the failed check.
- [ ] Every placeholder has **Revisit if**.
- [ ] No entry repeats a value that lives in FACTS.md.
