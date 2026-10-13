---
name: re-step-rationale
description: How to write the step and rationale entries in docs/steps.md and result files so a later agent, with none of this session's context, can see why each choice was made and does not redo or undo it. Load when writing steps.md, a handoff, or a task result.
---

# re-step-rationale

AGENTS.md already requires every step and decision in `docs/steps.md`. This skill is the format.

## Entry format
- **Step:** the action, command or file change, exact enough to repeat.
  **Decision:** the option chosen, and the alternatives that were rejected.
  **Rationale:** the constraint that forced it (platform, tool failure, hardware rule, evidence) and the failure it avoids.
  **Evidence:** tag plus citation (`[C] Class->method`, `[H] log file`, ...), when the step rests on a fact.

One or two lines per field. Do not rewrite older entries; add a new one that supersedes.

## Why
A resuming agent sees odd workarounds (a hand-installed JDK, smali instead of jadx for one method) and "fixes" them unless the reason is written down. When a test fails, the rationale names the assumption to check first.

## Anti-patterns
- Tautology: "Ran dexgrep. Rationale: to find classes."
- Rationale without the rejected alternative, when one was tried.
- Restating a fact that lives in FACTS.md; link it.
- Pasting decompiled code or personal data into the rationale.

## Good example
- **Step:** `dexgrep dump 'BaseReconnectBlueActivity;' onDisConnected`. **Decision:** dexgrep instead of jadx. **Rationale:** jadx is not installable in the cloud session; the question was a single constant. **Evidence:** [C] `const-wide/16 10000`.
