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

## 2026-10-13 — Phase 1 wrap-up

- **Step:** Wrote `targets/c900/recon-v2.md` (per-question answers, corrections, contradictions, what is still needed); pointed recon-v1, PLAN, OPEN-QUESTIONS and STATUS at it; added the new unknowns to PROTOCOL §10.
  - **Rationale:** Findings changed several earlier statements (version byte, retries, NAK, OTA interval, createBond), so a new brief is clearer than editing v1 in place; v1 stays as history.
- **Decision:** Phase 1 ends with Q05 partial. No client code, no watch contact, no app run, no server calls, no OTA send path touched.
  - **Rationale:** Stop condition (b) applies to Q05; the remaining static reads are listed in its result file and recon-v2 §5.


## 2026-10-13 REVIEW-PHASE1 (docs only)
- Step: Reviewed Phase 1 results Q04-Q09 against PROTOCOL/FACTS; no bootstrap (no check needed code).
- Decision (D-bond): retire FACTS §2 "no createBond in app code". Rationale: it was a negative jadx search; three named smali call sites are reproducible positive evidence. App bonds conditionally [C]; device side [U] (Q03); trigger conditions of two sites -> new C900-Q14.
- Decision (D-nolive): owner said no live test until necessary; next phase proposed as Phase 1b static (Q14 inbound remainder, Q15 HW-0 run sheet as a document). Both DRAFT.
- Step: closed Q04, Q06-Q09; Q05 closed partial; aligned recon-v2, PLAN (stale Q09/Q12 line), STATUS. Fixed a self-contradictory cell in the Q05 result. Report: targets/c900/tasks/results/REVIEW-PHASE1.md.

## 2026-10-13 — Phase 1b sign-off recorded

- **Decision:** Owner approved Phase 1b (2026-10-13): C900-Q14 static, C900-Q15 run sheet as a document only, plus an owner HCI-capture guide. Hardware stays parked.
  - **Rationale:** Owner wants no live test until necessary; all three items are static or documents.

## 2026-10-13 — C900-Q14 (Phase 1b)

- **Step:** Ran the seven steps in order on the box tree (present; no bootstrap needed).
  - **Decision:** Steps 2-7 done [C]; step 1 partial (key map and SpO2 only).
  - **Rationale:** Step stop rule: the step needed five parser classes not named in it. Writing the key map is still useful for a capture decoder.
- **Decision:** Wrote exact createBond conditions into FACTS §4 and PROTOCOL §3: three triggered paths, none unprompted.
  - **Rationale:** Acceptance asks for them, and they answer what the first contact must watch for (a bond prompt is an abort trigger in HW-0).

## 2026-10-13 — C900-Q15 HW-0 run sheet

- **Decision:** Wrote `targets/c900/tasks/HW-0-RUNSHEET.md`, marked DRAFT, zero writes, nothing run.
  - **Rationale:** Owner approved the document only.
- **Decision:** Banned `notify_log.py` in HW-3 in favour of a one-UUID snippet.
  - **Rationale:** The tool enables notify on all characteristics, including OTA ones on the never-touch list.
- **Decision:** Budget 3 connects, 6 reads, 30 min; abort on bond prompt, disconnect loop, OTA screen.
  - **Rationale:** C900-Q14 shows the app bonds only on watch request, so an unprompted prompt is new device behaviour worth stopping for.

## 2026-10-13 — HCI capture guide and Phase 1b wrap-up

- **Decision:** Wrote `docs/guides/HCI-CAPTURE-ANDROID.md`, linked from OPEN-QUESTIONS Q13, TARGET.md and HANDOFF.md.
  - **Rationale:** The owner asked for a plain-language guide. The guide's do-not list mirrors the never-touch OTA paths.
- **Decision:** Git-ignored `captures/`, `targets/*/captures/`, `*.btsnoop`, `btsnoop_hci.log*` and `bugreport*.zip`; checked with `git check-ignore`.
  - **Rationale:** These logs carry phone Bluetooth data and notification text, which is personal data.
- **Step:** Updated recon-v2 with a Phase 1b section.

## 2026-10-13 REVIEW-PHASE1B (docs only)
- Step: reviewed Phase 1b (Q14, HW-0 run sheet, capture guide) and all plan docs; smoke-ran btcap.py on the synthetic fixture (works, raw hex only).
- Decision: bonding wording made exact everywhere (three watch-side gates; the time-ack path is app-initiated but gated by feature b15 0x40). Rationale: "never unprompted" overstated it.
- Decision: Q14 step 1 remainder -> standalone C900-Q16. New DRAFT tasks Q17 (notify_log.py OTA-safe subscribe; tool not edited this pass), Q18 (DF decoder + synthetic fixture), Q19 (ingest owner capture, gate capture).
- Decision: recommended order Q17+Q18 -> Q16 -> owner capture -> HW-0 only for leftovers (NEXT-STEPS.md, DRAFT). Rationale: software first, remove hazards first, capture gives write-side facts a zero-write HW-0 cannot.
- Step: run sheet and capture guide safety/privacy gaps fixed; stale lines removed in PLAN, TARGET, recon-v2, STATUS. Report: targets/c900/tasks/results/REVIEW-PHASE1B.md.

## 2026-10-13 c900 INVARIANTS.md + guard test
- Step: added targets/c900/INVARIANTS.md (identity, frame, commands, bonding, OTA, process quirks with the wrong version each one replaced) and tests/test_c900_invariants.py (blocklist, checksum vector, rows present). Linked from TARGET, RECON-HIWEAR-APK, NEXT-STEPS; SOP note.
  - Rationale: owner asked to stop agents dropping quirks; several facts (byte 4 version, createBond, jadx constant swaps, OTA interval) were wrong once and could regress silently.

## 2026-10-13 — Phase 1c sign-off

- **Step:** Recorded owner approval of C900-Q16, Q17 and Q18; Q13 capture = later; HW-0 parked; Phase 3/4 deferred (OPEN-QUESTIONS checklist, PLAN §6c, STATUS).
  - **Decision:** Run order Q17 -> Q18 -> Q16, as instructed.
  - **Rationale:** Q17 removes the I-50 hazard before any tooling work; Q18 needs no LFS; Q16 needs the decompiled tree.

## 2026-10-13 — C900-Q17

- **Decision:** Deny by service as well as characteristic UUID.
  - **Rationale:** An OTA service could expose a characteristic UUID not in the list; skipping the whole service is the safe default.
- **Decision:** The deny list stays on even with `--only`, and a denied `--only` exits 2 before connecting.
  - **Rationale:** Spec; a typo in a flag must not reach an OTA characteristic.
- **Decision:** Rewrote INVARIANTS I-50 to the new state.
  - **Rationale:** New evidence of equal tag (tool code plus tests); the old row would now be false.

## 2026-10-13 — C900-Q18

- **Decision:** New script `tools/c900_decode.py`, btcap used as a library, no change to btcap.
  - **Rationale:** Spec; smallest blast radius.
- **Decision:** The fixture is generated by a committed script and a test checks the bytes match.
  - **Rationale:** Anyone can see every byte is synthetic, and it cannot drift.
- **Decision:** Hide message text by default and always mask the 0x0E/1 MAC.
  - **Rationale:** A real capture carries notification text and the watch's classic MAC; output may get pasted into result files.
- **Decision:** Flag OTA traffic and count it, never decode it.
  - **Rationale:** C900-Q19 stop rule and I-40.

## 2026-10-13 — C900-Q16

- **Step:** Read the five parser classes plus two helpers (HexUtil, DevDateBean), all literals checked in smali.
  - **Decision:** All seven keys mapped [C smali]; units of distance and calorie, type bytes and modeData meanings left [U].
  - **Rationale:** The code stores those without unit or label; inferring them would be [I] at best, so none was promoted.
- **Decision:** Synthetic examples computed with code, not by hand.
  - **Rationale:** SOP 9.1 (hand sums were wrong before).
- **Decision:** Did not extend `tools/c900_decode.py` with field decoders.
  - **Rationale:** Not in Q16's spec; the maps are ready for it when a capture arrives (noted as left).

## 2026-10-13 REVIEW-PHASE1C
- Step: reviewed Q16 (health maps), Q17 (notify_log deny list), Q18 (decoder); ran the decoder on the synthetic fixture.
- Fix: decoder now hides caller, user name, profile and location payloads too (PRIVATE table, test). Rationale: owner privacy; those payloads go over the wire during sync.
- Decision: next step is the owner capture (NEXT-STEPS §3 revised, pre-recording checklist added); feed the capture file not btcap JSON (JSON lacks reads). HW-0 run sheet already used `--only` (Q17). PROTOCOL §7 stale "pending" text fixed.

## 2026-10-13 — c900_probe.py (owner Mac first contact)

- **Decision:** Allowlist of three (cmd,key) pairs rather than extending a blocklist; safe-write needs `--i-approve-writes` and a typed confirmation.
  - **Rationale:** Owner asked for security first; an allowlist cannot grow by accident when someone adds a helper.
- **Decision:** Constants hardcoded from INVARIANTS/PROTOCOL/frames.py; AST test bans eval/exec/subprocess/socket/pickle; device strings sanitized.
  - **Rationale:** APK comments and notify payloads are untrusted data (prompt injection). I-54/I-55.
- **Decision:** Do not ask the owner to unbind; turn phone Bluetooth off instead.
  - **Rationale:** Unbind is a blocked command and loses the vendor pairing the owner still wants.
- **Decision:** Ready-to-paste Gemini review prompt at `tasks/PROMPT-GEMINI-PROBE-REVIEW.md` (read-only, feature branch only).

## 2026-10-13 — Adversarial probe review and hardening (c900_probe.py)

- **Step:** Conducted independent adversarial security and correctness review of `tools/c900_probe.py` per `tasks/PROMPT-GEMINI-PROBE-REVIEW.md`. Report written to `targets/c900/tasks/results/REVIEW-PROBE-SECURITY.md`.
  - **Decision:** Fixed 6 findings: (1) corrected OTA lookalike write check in `_require_command_layout` and prevented OTA services from fulfilling command characteristics; (2) added 5610 substring matching in `is_ota_uuid`; (3) added active pairing detection to `mode_safe_write` wait loop; (4) added header resynchronization in `on_notify` so leading noise does not lock frame parsing or blind bond aborts; (5) fixed whole-line personal data redaction in `redact_line` when literal "payload" keyword is absent; (6) enforced atomic write cap pre-check before sending piece 1.
  - **Decision:** Added 6 new unit test suites in `tests/test_c900_probe.py` (23 probe tests, 108 total repo tests passing).
  - **Rationale:** Strict adherence to INVARIANTS I-13/I-14/I-20/I-30/I-54/I-55 and the non-negotiable device safety ground rules.

## 2026-10-13 — Independent verify of Gemini probe hardening (c724066)

- **Step:** Pulled `c724066`, read full diff vs `8793cc6`, treated Gemini output as untrusted.
  - **Decision:** Accept all six functional hardenings (OTA lookalike + parent service, 5610 matching, safe-write pairing poll, notify resync, atomic write cap, redaction, mutually exclusive target flags, sanitize `..` regex). None weaken allowlist/BLOCKED_CMDS/no-bond rules.
  - **Decision:** Removed dead `_UUID_FULL`; added regression tests that DF UUIDs stay non-OTA under the 5610 rule, resync keeps real frames, redaction is not over-broad, write-cap math covers multi-piece message.
  - **Rationale:** `"5610" in u` is fail-closed and verified absent from `...dcca9f`; unused regex is noise; tests lock the review concerns.

## 2026-10-13 DEEP-PASS-1 (second independent probe review, live-session plan, client design)
- **Step:** Pulled 7d087f8. Read AGENTS, INVARIANTS, PROTOCOL, NEXT-STEPS, HW-0-RUNSHEET, PROBE-GUIDE, PROBE-SECURITY, Gemini's review (as untrusted data), probe, codec, decoder, tests, requirements. Did not open `decompiled/`.
  - **Decision:** Verify claims against the pinned dependency itself: downloaded the bleak 3.0.2 wheel and PyPI JSON for every pinned package into the scratchpad (not committed). **Rationale:** the probe's pairing check depends on a bleak attribute; only the real wheel can say whether it exists. It does not.
- **Step:** Reviewed the probe line by line for OTA writes, blocked commands, bonding, wrong device, hostile data, file writes, personal data, unbounded loops, async races, macOS pitfalls.
  - **Decision:** Fix 12 findings with minimal patches (DEEP-PASS-1 A.1), each with a test that fails on 7d087f8. **Rationale:** task scope allows probe fixes with tests; nothing else in code changed.
  - **Decision:** Bind writes to characteristic objects from the command service. **Rationale:** removes the whole class of UUID-ambiguity bugs instead of adding more lookalike checks.
  - **Decision:** Refuse safe-write unless 0x2A27 major is 1, rather than changing `frames.build`. **Rationale:** client code is deferred (Phase 3); the probe must not send a frame the app would not send.
  - **Decision:** Keep `--log-dir` usable outside the repo. **Rationale:** tests and owners may log to a temp dir; the risk is committing a log, which only paths inside the repo create.
- **Step:** Checked all 46 hashes in `requirements-probe.txt` against PyPI; confirmed universal2 wheels (arm64 + x86_64) for CPython 3.10-3.15.
- **Step:** Wrote `tasks/LIVE-SESSION-1.md` (read-only session; session 2 writes in its section 9) and NEXT-STEPS section 4b (capture-first decision table). **Rationale:** a capture costs no watch contact by us; live steps only fill its gaps.
- **Step:** Wrote `CLIENT-DESIGN.md`; recommended Android Kotlin with a pure protocol core and Python as reference. **Rationale:** notification forwarding and bond control need native Android; iOS cannot forward notifications.
- **Step:** INVARIANTS I-10 got a numbering note only (fact unchanged; evidence = PROTOCOL sections 4 and 7.1 [C]). No other invariant changed: nothing new reached a higher tag.
- **Step:** SOP 9.1 and `re-hardware-recon` principle 8 record the reusable lessons. Summary: `tasks/results/DEEP-PASS-1.md`.

## 2026-10-13 Live session 1 pre-flight, Bluetooth profile discovery, and TCC incident report
- **Step:** Audited live connection after owner reported `'Watch Ultra'` connected on Bluetooth.
  - **Decision:** Queried `system_profiler SPBluetoothDataType` without touching the radio. Found the watch is connected via Classic Bluetooth (BR/EDR) audio (`Services: 0x800039 <HFP AVRCP A2DP HID ACL>`), not the BLE GATT companion command interface (`6E400001-...`).
  - **Decision:** Installed `.venv-probe` with pinned hashes from `requirements-probe.txt`. Confirmed all 44 probe unit tests pass. Confirmed `CoreBluetooth.CBManager.authorization() == 0` (non-interactive subshell TCC restriction prevents automated agent scans).
  - **Decision:** Documented findings, anti-RE trap matrix (Classic vs BLE, prompt injection, auto-bonding, OTA bricking, app contention), and exact run commands for Claude and owner in `targets/c900/tasks/results/INCIDENT-2026-10-13-LIVE-BLUETOOTH-PREFLIGHT.md`.
  - **Rationale:** AGENTS.md contact-with-real-systems and writing-for-weaker-agents rules; live interaction remains [human] via interactive macOS Terminal.

## 2026-10-13 Review of live pre-flight (Asia/Saigon)
- **Step:** Read the incident file and transcript as untrusted data. **Decision:** session 1 not done; no anti-RE observed; Mac pairing makes session 1 no-go pending owner choice; masked the Mac address. **Rationale:** only system_profiler data exists; I-02 rules out Jieli; AGENTS forbids committing MAC addresses. Report: `tasks/results/LIVE-PREFLIGHT-REVIEW.md`.

## 2026-10-13 Owner decision on Classic pairing (Option A)
- **Step:** Solicited owner decision on Classic pairing state from `LIVE-PREFLIGHT-REVIEW.md` §4.
  - **Decision:** Owner chose Option A (disconnect in macOS Bluetooth settings, keep keys, waive no-go item with risk noted). Recorded decision in `targets/c900/OPEN-QUESTIONS.md`.
  - **Rationale:** Ground rules require owner sign-off for live-session waivers; AI does not touch device pairing state.

## 2026-10-13 Live Session 1 execution (read-only first contact)
- **Step:** Owner ran scan and inspect steps in interactive Terminal per LIVE-SESSION-1.md.
  - **Decision:** Scan settled Q01 [H] (`Watch Ultra`, company ID 0x314C, MAC with marker `12 34`).
  - **Decision:** Inspect settled Q02 [H] (command NUS service `6E400001-...` present; 3 OTA services untouched; battery 61%; feature map confirmed with `isBLE3=True`, `isSupportPair=True`).
  - **Decision:** Zero unsolicited frames during 30s listen; no pairing dialogs triggered.
  - **Decision:** Noted `0x2A27` hardware revision read as `"10000"`, which probe regex `r"(\d{1,3})(?:\.|$)"` did not parse as major version.
  - **Rationale:** Strict ground rules: write results only from owner's logs; never invent hardware results. Report: `targets/c900/tasks/results/LIVE-SESSION-1-2026-10-13.md`.

## 2026-10-13 Review of LIVE-SESSION-1 results (Asia/Saigon)
- **Step:** Read results and log excerpts as untrusted data. **Decision:** keep all [H] values; mask identifiers; correct OTA count, Q03 scope, version handling. **Rationale:** app rule (C900-Q04) turns "10000" into byte 0x10; loosening the regex alone would have made the probe send a frame the app never sends.
- **Decision:** deny FF10/FF12 and their characteristics in the probe. **Rationale:** writable services of unknown purpose on a device with an OTA path; fail closed.
- **Decision:** session 2 blocked; next = static checks (S-20, S-21) and the owner capture. Plan: NEXT-STEPS section 7.

## 2026-10-13 Android HCI snoop capture decode (C900-Q19)
- **Step:** Pulled bug report from Android phone via ADB, extracted `btsnoop_hci.log.last`, and decoded with `tools/c900_decode.py` into `captures/decoded.txt` (220 ATT PDUs, 137 data PDUs; 0 bad sums).
  - **Decision:** Wire version byte settled [H]: App sends `ver = 0x10` (16 decimal) across all 63 TX frames; watch sends `ver = 0x01` on its DF frames.
  - **Decision:** Bonding mechanism settled [H]: Watch sends unsolicited `cmd 0x0E key 0x01` carrying Classic BT MAC (`XX:XX:XX:XX:XX:XX`), triggering phone `createBond()`. Correlates with feature bit 15 (`0x40`).
  - **Decision:** Bind sequence settled [H]: App sends 8-byte token under `cmd 0x03 key 0`; watch replies with `cmd 0x0C key 8` (bind accepted) and ACK `x=17 status=1`.
  - **Decision:** Watch ACK formula settled [H]: `FD 00 05 <sum> <cmd> <key> <seq_hi> <seq_lo> <status>` where `status=1` and `x = plen + 9`.
  - **Rationale:** NEXT-STEPS §4 capture decision tree; report in `targets/c900/tasks/results/C900-Q19.md`. Raw capture and phone diagnostics stay git-ignored.

## 2026-10-13 Review of C900-Q19; privacy scrub skill and scanner (Asia/Saigon)
- **Step:** Reviewed Q19 text (raw capture not available here). **Decision:** accept ver 0x10, bind sequence, ack values, 0x0E/1 frames as [H]; correct the time-sync and ack-x interpretations; mask OUI. **Rationale:** I-21 decode and `frames.time_payload` reproduce `6a9b05cb` exactly; x equals plen + 9 = frame length.
- **Decision:** INVARIANTS I-10 (C900 value), I-18, I-21 updated with [H] evidence. **Rationale:** capture is higher evidence than [C]/[I].
- **Step:** Added `tools/privacy_scan.py` (stdlib) + tests and skill `re-privacy-scrub`. **Rationale:** three leaks in one day came from agents writing results by hand; a mechanical check plus a written procedure catches the repeat pattern. Kept out of `rw.py lint` for now because test fixtures hold synthetic addresses; FIXES Open tracks wiring it into lint.

## 2026-10-13 Hardening before live-agent handoff (Asia/Saigon)
- **Decision:** move safety from prompts into checks: lint rejects captures/probe logs and personal data; opt-in pre-commit hook; probe permission preflight. **Rationale:** each of today's incidents (leaks, hung scan, tempting "fixes") came from an agent following prose; mechanical checks hold even when the brief is skipped.
- **Decision:** one-page `tasks/AGENT-BRIEF.md` instead of long pasted prompts. **Rationale:** a weaker agent gets state, prohibitions and commands in one place.
- **Not done (needs owner OK):** codec `ver` parameter (Phase 3 code); history rewrite of leaked commits.

## 2026-10-13 HCI pairing events check (C900-Q19 second pass, Asia/Saigon)
- **Step:** Decoded all HCI commands, events, and L2CAP CIDs from `captures/btsnoop_hci.log.last` to verify link-layer pairing following the time-sync ack and `cmd 0x0E key 1` announcements.
  - **Decision:** Wire pairing status settled [H]: Time sync ACK (t=2.732s) triggers `HCI_Remote_Name_Request` (t=2.764s) targeting the derived Classic BT address (`ble_mac last byte ^ 0x55`, confirming I-30 path #3).
  - **Decision:** Zero Classic connection or keys on the wire [H]: All 3 `HCI_Remote_Name_Request` commands timed out after 12.8s (status 0x04, `Page Timeout`). No `HCI_Create_Connection`, `Authentication_Complete`, or link keys occurred.
  - **Decision:** Zero LE SMP or link encryption [H]: Zero packets on L2CAP CID 0x0006; zero `HCI_LE_Start_Encryption` or `Encryption_Change` events. LE link remained in cleartext.
  - **Rationale:** AGENT-BRIEF task; report in `targets/c900/tasks/results/C900-Q19.md` Section 7. Event names and relative times only; no addresses.


## 2026-10-13 Codec ver parameter and session 2 readiness (Asia/Saigon)
- **Step:** Owner approved the codec change. **Decision:** `ver` is a build() parameter with the old default, so all earlier vectors are unchanged; the probe sends the 0x2A27-derived value only if it is reviewed (0x01 default, 0x10 C900 [H]). **Rationale:** matches the app byte for byte without letting an unexpected device value through.
- **Decision:** SimWatch acks with x = acked frame length. **Rationale:** I-18 [H]; still a simulator (consistency only).
- **Decision:** reviewed Q19 section 7; recorded excerpt length typos. Session 2 needs the owner's written approval; `find` first.

## 2026-10-13 Owner QR observation (Asia/Saigon)
- **Decision:** record as app UX [H owner]; protocol does not need it (probe and capture evidence). **Rationale:** separate "how the app picks a device" from "what the watch requires". Open S-22 (smali of scan-code screen) to rule out a key in the QR.

## 2026-10-13 Live Session 2 pre-flight and owner approval (Asia/Saigon)
- **Step:** Verified workspace on `feat/c900-hiwear-plus`, all 177 tests pass, `rw.py lint` 0 problems.
- **Step:** Reviewed `AGENT-BRIEF.md` and `LIVE-SESSION-1.md` Section 9.
- **Decision:** Recorded owner written approval for `find` safe-write command in `targets/c900/OPEN-QUESTIONS.md`. Prepared exact interactive Terminal command for owner execution with `--i-approve-writes`.
  - **Rationale:** AGENTS.md ground rules require owner written approval for live safe-writes naming the exact command; probe execution is performed by the owner in an interactive macOS Terminal session, never by the AI.

## 2026-10-13 Live Session 2 execution (safe-write find, Asia/Saigon)
- **Step:** Owner ran `safe-write --command find` in interactive Terminal.
  - **Decision:** Fail-safe gate verified: typed `j` aborted immediately without sending bytes (`SAFETY_STOP confirmation mismatch; nothing sent`).
  - **Decision:** Successful second run settled: wire `ver=0x10` confirmed working live against `0x2A27` read [H]; single 10-byte piece sent (`TX piece 1/1 len=10`) [H]; immediate ACK `x=0x000a x_is_frame_len=True status=1` [H]; watch executed alert ("the bracelet has been found!" with vibration) [H owner].
  - **Decision:** Confirmed invariant I-18 live (ack field x = frame length = 10); narrowed invariant I-35 (hardware executes find alert without requiring prior bind).
  - **Rationale:** Strict adherence to AGENTS.md, `re-privacy-scrub`, and safety protocol. Report: `targets/c900/tasks/results/LIVE-SESSION-2-2026-10-13.md`.

## 2026-10-13 Post-Session 2 doc sync (AGENT-BRIEF, NEXT-STEPS, Asia/Saigon)
- **Step:** Synchronized task state in `targets/c900/tasks/AGENT-BRIEF.md` and `targets/c900/NEXT-STEPS.md` to reflect Session 2 `find` completion [H] and remaining unapproved commands (`time`, `message`).
  - **Rationale:** AGENTS.md requirement: brief and plan docs must reflect true workspace state so any subsequent agent has exact context without having to deduce it.

## 2026-10-13 S-21 / S-22 (Asia/Saigon)
- **Question that needed the code:** S-21 (are FF10/FF12 used by the app?) and S-22 (does the QR carry a key?). Both [U] and relevant to client safety. **Decision:** read the pinned LFS copy with androguard instead of a full jadx rebuild (jadx unreachable). **Result:** FF10/FF12 unused; QR = MAC only.

## 2026-10-13 Owner "do all": S-21/S-22, session 3 sheet, Phase 3a (Asia/Saigon)
- **Decision:** S-21/S-22 via androguard on the pinned copy (done, pushed). Session 3 (message, time) approved by the owner's "do all"; written as a run sheet because only the owner can run radio steps.
- **Decision:** Phase 3 platform Android Kotlin per CLIENT-DESIGN; start with a pure Kotlin core so it can be built and tested here; the Python codec stays the reference through a shared vector file. **Rationale:** cloud cannot reach Google Maven; the core holds all protocol and safety logic anyway.
- **Decision:** bind (cmd 3) not in the allowlist. **Rationale:** may displace the Hiwear Plus binding; needs an explicit owner choice (CLIENT-DESIGN section 10 item 2).

## 2026-10-13 Live Session 3 execution (safe-write message, Asia/Saigon)
- **Step:** Owner ran `safe-write --command message` in interactive Terminal.
  - **Decision:** Transmitted 24-byte message frame in two pieces (`TX piece 1/2 len=20`, `TX piece 2/2 len=4`) per ATT pacing rules [H].
  - **Decision:** Watch emitted `cmd 0x0E key 1` (Classic Bluetooth MAC announcement) immediately following transmission [H].
  - **Decision:** Probe `BOND_TRIGGERS` rule triggered safety stop (`SAFETY_STOP bond-trigger inbound cmd=0x0e key=1`, `DISCONNECT ok`, exit code 3) [H]. Zero pairing attempts or link keys occurred; protected system pairing posture.
  - **Rationale:** Strict adherence to safety checks; report written in `targets/c900/tasks/results/LIVE-SESSION-3-2026-10-13.md`.
