# Ready-to-paste: Claude improve-plan pass

Copy everything inside the fence below into Claude (cloud or local). Feature branch only.

```
You are working in THAI-passport/reWatch on branch feat/c900-hiwear-plus (or the branch you were given).

Pass type: IMPROVE-PLAN (critique and improve docs). Not implementation. Not a deep decompile.
Never touch a watch. Never install/run the vendor app. Never push main. No PR unless asked. No new client features. Keep PLAN.md and OPEN-QUESTIONS.md marked DRAFT.

Read in this order (do not slurp decompiled/):
1) AGENTS.md (ground rules)
2) targets/c900/recon-v1.md
3) targets/c900/PLAN.md
4) targets/c900/OPEN-QUESTIONS.md
5) targets/c900/tasks/RECON-HIWEAR-APK.md
6) targets/c900/tasks/STATUS.md
7) Skim PROTOCOL.md / FACTS.md only where recon-v1 is thin

Optional: light targeted rg only to sanity-check a claim already in recon-v1 (one class/file). Bootstrap (bash tools/cloud_bootstrap.sh) only if that check needs code and the tree is missing — otherwise skip (saves LFS bandwidth).

Your job — critique and improve for clarity, gaps, priority, and risk:
- recon-v1.md: missing findings? weak tags? decisions incomplete?
- PLAN.md: phases/gates/risks coherent with recon-v1 decisions?
- OPEN-QUESTIONS.md: each C900-Q## self-contained for a subagent (inputs, method, gate, acceptance, output path)? Priorities right? Deferred items correctly fenced?
- STATUS.md / RECON-HIWEAR-APK.md: consistent with question IDs?
- Flag contradictions with PROTOCOL/FACTS; do not silently invent [C] claims.

Edit the docs in place. Keep DRAFT banners. Append docs/steps.md with what you changed and why. If you hit a real pitfall, append targets/c900/LOG.md.

Do NOT: implement client code, start Phase 1 research beyond sanity-checks, open PAR/native RE, or send anything over BLE.

Deliverable: short report in chat (and optional tasks/results/IMPROVE-PLAN.md) listing changes. unittest + rw.py lint if you touched code (prefer docs-only). Commit on the feature branch; push the feature branch only.

STOP after the improve-plan pass; do not begin Phase 1 question execution.
```
