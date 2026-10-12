# Task: Hiwear Plus recon — Phase 0 plan review (then optional Phase 1)

**Cloud setup (Phase 1 / claim checks only):** [docs/CLOUD-SETUP.md](../../../docs/CLOUD-SETUP.md) — `bash tools/cloud_bootstrap.sh` → `PASS`.  
**Start here:** [../recon-v1.md](../recon-v1.md) (consolidated findings + decisions).
**Drafts to review:** [../PLAN.md](../PLAN.md) · [../OPEN-QUESTIONS.md](../OPEN-QUESTIONS.md) (both **DRAFT pending owner review**).

Self-contained brief for Claude, Gemini, Antigravity, or any other agent. Follow reWatch `AGENTS.md`.

**Main goal is not implementation.** First revise the plan and open questions; only after owner approves Phase 0 may anyone run a deeper decompile pass.

---

## Starter prompt (paste to the cloud AI) — Phase 0 only

```
You are working in THAI-passport/reWatch on branch feat/c900-hiwear-plus (or the branch you were given).
Main goal: revise the C900/Hiwear Plus PLAN and OPEN-QUESTIONS — not implementation, not a big decompile pass.
Never touch a watch. Never push main. No PR unless asked. No new client features.

Phase 0 only:
1) Read AGENTS.md ground rules, then targets/c900/recon-v1.md (start), PLAN.md, OPEN-QUESTIONS.md, PROTOCOL.md, FACTS.md, LOG.md, docs/steps.md, TARGET.md, tasks/STATUS.md, and this file (RECON-HIWEAR-APK.md).
2) Bootstrap is OPTIONAL. Run `bash tools/cloud_bootstrap.sh` only if a light claim sanity-check needs the decompiled tree; otherwise skip (saves ~105 MB LFS bandwidth).
3) Light targeted rg only to sanity-check existing claims — do not start new research areas. Do not read the whole decompiled tree.
4) Edit PLAN.md and OPEN-QUESTIONS.md (keep DRAFT until owner signs off): revise goals, phases, gates, risks, priorities, how-to-answer, costs. Mark implementation-only items Deferred. Relabel client/c900 work as deferred if not already.
5) Write targets/c900/tasks/results/RECON-HIWEAR-APK.md (Phase 0 report). Append docs/steps.md. unittest + lint if you touched code (you should not need to). Commit/push the feature branch if asked.
6) STOP and report for owner sign-off. Do not start Phase 1.
```

---

## Phase 0 — plan review (deliverable only)

### Allowed
- Read **recon-v1.md** first, then docs listed in the starter prompt (and `results/S2`…`S9` if useful).
- Light targeted `rg` / single-file peeks **only** to sanity-check a claim already in PROTOCOL/FACTS (e.g. confirm a CommandID value). Prefer not to bootstrap.
- Edit `targets/c900/PLAN.md` and `targets/c900/OPEN-QUESTIONS.md`.
- Update `docs/steps.md`, this task's result file, and STATUS row for Phase 0.
- Fix doc typos that block understanding.

### Forbidden in Phase 0
- New decompile passes or apktool smali sweeps beyond what bootstrap already produced (and bootstrap itself is optional).
- New client code, scanners, session logic, or OTA/face helpers (`client/c900` is **deferred**).
- Expanding research into PAR native, full HryFine compare, or Cus5610 beyond noting them as questions.
- Hardware, installs of the vendor app, vendor server calls.
- Starting Phase 1 without written owner approval of PLAN + OPEN-QUESTIONS.

### Phase 0 deliverables
1. `targets/c900/PLAN.md` — revised goals, phases, gates, risks (still marked DRAFT until owner clears it).
2. `targets/c900/OPEN-QUESTIONS.md` — each question: why it matters, priority, evidence so far, how to answer (static / hardware / capture), cost estimate, dependencies; implementation-only → **Deferred**.
3. `targets/c900/tasks/results/RECON-HIWEAR-APK.md` — Phase 0 report (what changed in the drafts, what you sanity-checked, explicit STOP).
4. **STOP** and ask for owner sign-off.

### Phase 0 report format

```markdown
# RECON-HIWEAR-APK result — Phase 0

Date: YYYY-MM-DD (Asia/Saigon)
Agent: <name>
Branch / commit: <...>

## Summary
Plan/open-questions review only. Phase 1 not started.

## Changes to PLAN.md
- ...

## Changes to OPEN-QUESTIONS.md
- ...

## Sanity-checks (if any)
| Claim | How checked | Outcome |
|---|---|---|

## Bootstrap used?
no | yes (why)

## Owner sign-off needed
List decisions / priority calls.

## STOP
Phase 0 complete. Awaiting owner approval before Phase 1.
```

---

## Phase 1 — deeper static (only after owner approves Phase 0)

Owner must explicitly approve which question IDs from `OPEN-QUESTIONS.md` are in scope.

### Then allowed
- `bash tools/cloud_bootstrap.sh` if the tree is missing.
- Targeted decompile/smali/`rg` limited to approved questions.
- Update PROTOCOL/FACTS/LOG/steps; optional synthetic tests (no vendor dial binaries in git).
- Result file section “Phase 1”.

### Still forbidden
- Client feature work (deferred to Phase 3 in PLAN.md).
- OTA/watch-face/firmware send paths.
- Hardware without a separate HW approval.
- Push to `main` / unsolicited PR.

### Token-saving (Phase 1 only)

Do **not** slurping the whole `decompiled/` tree. Start from:

| Topic | Paths under `targets/c900/decompiled/sources/` |
|---|---|
| GATT / MTU | `com/myled/HiwearPlus/BleConstants.java`, `.../ble/MBleManager.java` |
| Frames | `.../ble/IssuedUtil.java`, `.../ble/utils/NotifyWriteUtils.java`, `.../AckPackageConfigUtils.java` |
| Commands | `.../ble/CommandID.java`, `SettingIssuedUtils.java`, `MsgPushHelper.java`, `GeneralUtils.java` |
| Inbound | `.../ble/infoutils/BleDataUtils.java` |
| OTA D5/D6 | `.../ble/ota/CommandUtils.java`, `OTAUtils.java`, `OTANotifyWriteUtils.java` |
| Dial.bin | `.../function/dial/activity/DialDetailActivity.java`, `.../utils/StringUtils.java` |
| PAR (if approved) | `com/bluetrum/abpartool/ParTool.java`, `.../WatchFaceEditActivity.java` |

Write findings incrementally. If budget is low: stop, commit, report.

---

## Hard rules (all phases)

- Static only unless a later HW task says otherwise. Never install/run the vendor app. Never write to a watch here.
- Dangerous command ids stay blocked: `0x01, 0x04, 0x06, 0x07, 0x0D, 0x13`.
- Evidence tags `[C][V][H][W][I][U]`. Pin rule. No secrets. No emoji.
- Log to `docs/steps.md`, target `LOG.md`, `FACTS.md`, `PROTOCOL.md`, skills/SOP as applicable (AGENTS.md).
- Feature branch only.

## Overall product goal (context)

Long-term: open-source ad-free C900 client via the Hiwear Plus protocol. **This task’s job is the plan and (later) answers to approved questions** — not building that client yet.
