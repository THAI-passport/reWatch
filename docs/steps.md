# Steps log (reWatch)

Chronological record of every step and every decision with its rationale.
Times are Asia/Saigon (UTC+7). Append as work proceeds; do not rewrite history.
Required by AGENTS.md.

---

## 2026-10-12 — seed and landscape

- **Step:** Seeded reWatch from reWork; adapted README/AGENTS/CLAUDE for smartwatches; added skills (re-jieli, re-ble-android-patterns, re-watch-targets, re-capture-ingestion) and SOP / FROM-REBEAMBOX.
  - **Rationale:** Separate watch RE from beam-box work; reuse tooling patterns without mixing targets.
- **Step:** Imported owner-supplied budget-smartwatch landscape as `docs/recon/budget-smartwatch-landscape.md` with flaws table; all claims tagged [W].
  - **Rationale:** External write-up is useful as a seed but must not be treated as confirmed.

## 2026-10-12 — combined t900-c900 pass (later superseded for C900)

- **Decision:** Treat T900 and C900 as one combined target `t900-c900` for the first benchmark pass.
  - **Rationale:** Landscape doc and early owner notes treated them as the same HryFine-class stack; one gate set was faster for a dry run of the workflow.
- **Step:** G0–G5 on `t900-c900`: brief, acquire notes, surface map, PROTOCOL from [W] sources, client/simulator built ahead, handoff + hardware task pack.
  - **Rationale:** Prove the reWatch loop end-to-end before hardware; mark everything built-ahead / [W].
- **Decision:** Do not open a PR; stay on feature / integration branches; never push main.
  - **Rationale:** Owner standing rule.

## 2026-10-13 — C900 identity: main verification and folder reconciliation

- **Step:** Owner stated the C900 uses Hiwear Plus, not HryFine / HiWatch Pro as the landscape assumed.
  - **Rationale:** Correct package identity before more RE; wrong app wastes the whole gate set.
- **Decision:** One target directory per watch. Fold `targets/t900-c900` into `targets/c900` (legacy notes under `sources/`) and keep `targets/t900` separate; add t900 PROTOCOL section 9 pointer.
  - **Rationale:** Combined folder encoded a false identity claim; splitting prevents cross-contamination of FACTS/PROTOCOL.
- **Step:** Commit `9c9f85e` on `feat/c900-hiwear-plus` (folder reconciliation).

## 2026-10-13 — package choice, pin, decompile

- **Decision:** Pin Hiwear Plus `com.myled.HiwearPlus` 2.0.1 (version code 31) from APKPure as the C900 companion artifact.
  - **Rationale:** Owner named Hiwear Plus; 2.0.1 was the available release; SHA-256 recorded so rebuilds refuse drift.
- **Step:** Download XAPK, verify hashes (XAPK `5fa761a4...8952`; base APK `931efc77...3a5a`; abi `4c71b281...7330`); jadx into `targets/c900/decompiled` (`--max-heap 3g`, exit 3 accepted); apktool `-s` tree for resources.
  - **Rationale:** Static-only; rebuild_analysis records BUILD-INFO; jadx exit 3 is normal for partial failures.
- **Decision:** Leave COPY_LOCATION open initially (owner storage); later overridden by repo-copy exception.
  - **Rationale:** Ground rule 3 forbade committing the binary; floating `version=latest` URL needs an exact owner copy.

## 2026-10-13 — static survey (G2) and Gemini merge

- **Step:** First-pass code read: BleConstants, IssuedUtil, CommandID, SettingIssuedUtils, OTAUtils, scan filters; write PROTOCOL sections 1–10, FACTS (identity + annotated old claims), TARGET gates, LOG, task STATUS/SW/HW, SOP 9.1; mark `frames.py` built-ahead with wrong opcodes called out.
  - **Rationale:** Capture [C] framing before touching the client; keep dangerous ops out of the codec until confirmed.
- **Step:** Merge Gemini document as untrusted data into `targets/c900/sources/gemini-hiwear-re.md`; list disputes in FACTS; verdict: header/checksum/ack right, opcodes and MTU/service claims wrong (0x04/0x07 dangerous).
  - **Rationale:** Third-party RE can accelerate framing notes but must not drive opcodes; owner required a kept copy + dispute list.
- **Step:** Commits `bdc769c`, `3cf8337`.

## 2026-10-13 — owner-approved archive (REPO_COPY)

- **Decision:** Zip the exact original XAPK into `resources/c900/hiwear-plus-2.0.1.xapk.zip` (Git LFS), record REPO_COPY + hashes, allow by exact `.gitignore` path; update rebuild + lint.
  - **Rationale:** Owner explicit override of the no-binaries rule for this one artifact so cloud agents can rebuild without APKPure; zip SHA-256 `80066200...570e`, 104797741 bytes (>100 MB → LFS).
- **Step:** Install git-lfs 3.5.1 to ~/tools; `.gitattributes`; `from_repo_copy` in rebuild_analysis.py; `pinned_repo_copies` lint; tests; push LFS object. Commit `566f715`.
  - **Rationale:** Pointer files without LFS pull must fail loudly; undeclared files under resources/ must fail lint.

## 2026-10-13 — this pass (smali, OTA framing, client fix, tasks S2/S4/S5/S7/S8/S9)

- **Step:** apktool decode **without** `-s` into `work/smali`; confirm time year offset `add-int/lit16 … -0x7d0` in `SettingIssuedUtils.settingSysTime`.
  - **Rationale:** Jadx had printed `BaseResp.CODE_ERROR_PARAMS` (-2000); same substitution pitfall as reBeamBox; smali is authoritative for literals.
- **Step:** Read OTAUtils / CommandUtils / OTANotifyWriteUtils / DialDetailActivity / WatchFaceEditActivity / ParTool usage; document D5/D6 OTA framing, dial.bin obfuscated Base64, PAR path, Cus5610 inventory; rewrite PROTOCOL section 6. No client send path.
  - **Rationale:** Owner asked for watch-face format + OTA framing documented only; ground rule forbids OTA/firmware use.
- **Step:** Fix `client/c900/frames.py` to CommandID opcodes; add `BLOCKED_CMDS` {0x01,0x04,0x06,0x07,0x0D,0x13}; `time_payload`; tests green.
  - **Rationale:** Built-ahead opcodes were wrong and unsafe; blocklist enforces the dangerous-command list in code.
- **Step:** Progress S2, S4, S5, S7, S8, S9 result files; update FACTS, TARGET, STATUS, LOG, root LOG/FIXES, SOP 9.1, re-static + re-ble-android-patterns skills, README/setup_tools LFS note.
  - **Rationale:** AGENTS.md requires every applicable doc updated in the same commit as the pass.
- **Decision:** Create `docs/steps.md` and require append-on-every-step in AGENTS.md (all three repos).
  - **Rationale:** Owner instruction 2026-10-13; weaker agents and later passes need the decision trail, not only FACTS/PROTOCOL outcomes.

## 2026-10-13 — steps log rule across repos

- **Step:** Create `docs/steps.md` (backfilled for C900/Hiwear Plus); add AGENTS.md rule. Same rule + template on reWork (`feat/steps-log`), same rule + brief backfill on reBeamBox (`feat/steps-log`).
  - **Rationale:** Owner instruction; keep the decision trail with the code, not only in chat.

## 2026-10-13 — LFS cost check + external recon task

- **Step:** Verified GitHub Free LFS quotas from official docs (10 GiB storage + 10 GiB bandwidth/month); confirmed overage behaviour depends on budget/$0 vs payment method; confirmed CI `actions/checkout@v4` does not set `lfs: true` (default false). Billing usage API not readable with current `gh` scopes (`user` scope missing); no billing settings changed.
  - **Rationale:** Owner asked for exposure of the ~105 MB archive before more agents pull it; public clones and `lfs: true` CI would burn owner bandwidth.
- **Decision:** Add `targets/c900/tasks/RECON-HIWEAR-APK.md` as a self-contained brief for another AI; link from STATUS; remind agents to `git lfs pull -I` only the one archive.
  - **Rationale:** Parallelise remaining static questions (PAR, dial.bin, OTA details, remaining cmds) without redoing known PROTOCOL/FACTS work.

## 2026-10-13 — cloud bootstrap for low-token recon

- **Step:** Add `docs/CLOUD-SETUP.md` and idempotent `tools/cloud_bootstrap.sh` (pinned jadx 1.5.6 / apktool 3.0.3 hashes, LFS pull -I one zip, rebuild, PASS/FAIL). Extend `RECON-HIWEAR-APK.md` with starter prompt, cloud-setup link, and token-saving class list.
  - **Rationale:** Owner wants Claude Code cloud / Antigravity to run recon with minimal tokens; one command to PASS, then scoped rg from known classes instead of slurping the decompiled tree.

## 2026-10-13 — Phase 0 plan-first recon (owner feedback)

- **Decision:** Split RECON-HIWEAR-APK into Phase 0 (plan/open-questions only) and Phase 1 (deeper decompile only after owner approves Phase 0). Draft `PLAN.md` and `OPEN-QUESTIONS.md` now so a cloud AI reviews rather than invents. Mark `client/c900` feature work deferred (G4 deferred).
  - **Rationale:** Owner: main goal is not implementation; revise plan and questions before more decompile. Saves LFS/tokens and avoids building the wrong client.
- **Step:** Rewrite starter prompt for Phase 0; bootstrap optional (only if a claim check needs code).

## 2026-10-13 — recon-v1 + assignable questions + improve-plan prompt

- **Step:** Write `targets/c900/recon-v1.md` consolidating package/pin, Bluetrum stack, transports, frame, commands, OTA/faces, server summary, Gemini verdict, and Decisions from findings. Polish OPEN-QUESTIONS into assignable C900-Q## specs; align STATUS; point RECON-HIWEAR-APK at recon-v1; add `tasks/PROMPT-CLAUDE-IMPROVE.md`.
  - **Rationale:** Owner asked for a findings snapshot with decision trail, subagent-ready questions, and a pasteable Claude critique pass before more work.
- **Decisions logged (see recon-v1):** D-stack deprioritise Jieli; D-face OTA-class deferred; D-block blocklist; D-client defer features; D-lfs single REPO_COPY; D-phase0 gate; D-identity Hiwear-only target; D-gemini opcodes from [C] only.


## 2026-10-12 improve-plan pass (docs only)
- Step: Critiqued recon-v1, PLAN, OPEN-QUESTIONS, STATUS, RECON-HIWEAR-APK. Added run-order rule (P0 = importance; static first), Who/stop rules, C900-Q13 (existing owner capture first, per software-first rule), smali checks for 100 s timeout and OTA interval 300/500, `[owner]` tag weight, STATUS fixes for Q09/Q12. Report: targets/c900/tasks/results/IMPROVE-PLAN.md.
  - Rationale: questions must be runnable by an agent that has not seen this conversation, and nothing may run before sign-off.

## 2026-10-13 — Phase 0 sign-off recorded

- **Decision:** Owner sign-off (delegated by the owner to the requesting agent, 2026-10-13): Phase 1 approved for C900-Q04, Q05, Q07, Q08, Q06 optional; Q09 approved as static inventory only with no server calls; Q12 parked; Q13 stays open pending the owner's answer. PLAN marked "Approved for Phase 1"; DRAFT kept for everything outside that scope.
  - **Rationale:** The approved items are static and document-only, and they feed listen-only and first-contact planning. Q12 touches the OTA/DFU firmware path and has no near-term use. Q13 depends on a fact only the owner has. Phase 1 work has not started.

## 2026-10-13 — C900-Q13 answered

- **Decision:** Owner answered Q13: No capture yet (2026-10-13). Q01-Q03 remain live hardware tasks behind HW-0.
  - **Rationale:** With no capture, nothing settles Q01-Q03 without new watch contact. Later option: the owner can record an Android HCI snoop log of Hiwear Plus pairing and time sync on their own phone. It is cheap and owner-run, and worth doing before HW-0. It is the owner's choice; the AI does not request it. No Phase 1 work started.

## 2026-10-13 — Phase 1 started; C900-Q08 contacts path

- **Step:** Pulled `feat/c900-hiwear-plus` (HEAD 5b9594f). Ran approved Phase 1 in the order the owner gave: Q08, Q04, Q05, Q07, Q09, Q06. Used the existing box tree (`decompiled/` jadx, `work/smali/` apktool); no re-decompile.
  - **Rationale:** The trees already exist and match the pinned 2.0.1 build. Re-decompiling costs time and adds nothing.
- **Step:** Q08: checked both `OTAUtils` call sites with main=4 in smali; listed every `OTAUtils.<init>` site in the app; traced the contact capability bit and the inbound MD5 report.
  - **Decision:** Q08 done [C]. Contacts are OTA-class (main 4, sub 1); no DF opcode. Documented the file layout for reference only.
  - **Rationale:** The acceptance criterion is a verified [C] note; smali settles the jadx literals, and the full call-site list rules out a second path.

## 2026-10-13 — C900-Q04 command keys

- **Step:** Checked the 100 s ack timeout in smali first, as the task asked: `0x186a0` at both arm sites. Then read the send loop, the ack/NAK path, every `getSendByte` caller, and the message-type tables.
  - **Decision:** Q04 done [C]. 100 s confirmed; PROTOCOL §3/§4 corrected (version byte, retry rule, NAK x=3); §5.1 tables added.
  - **Rationale:** Acceptance needs each row with layout and source; every literal jadx printed as a named constant was replaced by its smali value, because jadx inlines by value and picked wrong names.
- **Decision:** Did not edit `client/c900/frames.py` (FIXED_BYTE comment, SimWatch ack x).
  - **Rationale:** No client work in Phase 1. Recorded in FACTS as [I] / correction for Phase 3.

## 2026-10-13 — C900-Q05 inbound map (partial)

- **Step:** Read the inbound dispatcher top to bottom, the device-control handler and the feature parser.
- **Decision:** Stopped Q05 as partial when smali showed three app-code `createBond` calls that conflict with FACTS §2 and PROTOCOL §3.
  - **Rationale:** OPEN-QUESTIONS stop condition (b): a value that conflicts with FACTS.md is recorded there and no winner is picked. Verified by an app-wide smali search before recording, so the conflict is real and reproducible.
- **Decision:** Wrote the mapped part (14 cmds, 0x0C keys, feature bits) and listed six next reads in the result file.
  - **Rationale:** A partial result with exact next steps lets the next pass resume without re-reading the dispatcher.

## 2026-10-13 — C900-Q07 OTA ready reply and interval

- **Step:** Read the 0x81/0x82/0x83 handler, the field initializer, the OTA send runnable and write callback in smali; searched all dex dirs for readers of `sendInterval`.
  - **Decision:** Q07 done [C]. The 300 vs 500 ms conflict is resolved: 500 is the init, 300 is the zero-reply substitute, and the value is never applied. Pacing is callback-driven with a 10 ms sleep.
  - **Rationale:** The task asked to resolve the conflict, not to choose a number. Following every read of the field showed neither value controls timing, which is the fact a future client needs.
- **Decision:** Documented width edge cases (signed group/timeout bytes) and the missing reply checksum.
  - **Rationale:** These are the "false safe to send" traps Q07 exists to prevent. Client must not implement.

## 2026-10-13 — C900-Q09 server inventory

- **Step:** Parsed the single Retrofit interface with a script (verb, path, method, parameter style), listed base-URL constants, and read the request-signing helper for its shape.
  - **Decision:** Q09 done [C]: 70 endpoints, 7 hosts, MD5 `sign` scheme. Secret values left out on purpose.
  - **Rationale:** The owner approved static inventory only, with no server calls. AGENTS.md forbids committing tokens; the algorithm shape is enough to know the client must not call these, and recording the key would add risk with no benefit.

## 2026-10-13 — C900-Q06 dial decode and trim

- **Step:** Budget allowed Q06. Verified the trim offsets and the token swap in smali, re-derived the three token MD5s locally, and listed which screens trim.
  - **Decision:** Q06 done [C]. Trim is store-screen only and gated by a watch-reported flag; purchased faces are never trimmed.
  - **Rationale:** Acceptance asks for field offsets and token seeds; smali settles both. The per-screen finding closes a PROTOCOL §6.5 unknown at no extra cost.
- **Decision:** No unittest added.
  - **Rationale:** With synthetic bytes and no vendor dial, a test would only check my own re-implementation, which is not evidence about the app.
