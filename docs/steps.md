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

## 2026-10-13 Live Session 3 execution (safe-write message & time, Asia/Saigon)
- **Step:** Owner ran `safe-write --command message` in interactive Terminal.
  - **Decision:** Transmitted 24-byte message frame in two pieces (`TX piece 1/2 len=20`, `TX piece 2/2 len=4`) per ATT pacing rules [H].
  - **Decision:** Owner confirmed notification `"reWatch test"` appeared on watch display [H owner].
  - **Decision:** Watch emitted `cmd 0x0E key 1` (Classic Bluetooth MAC announcement) immediately following transmission [H]. Probe `BOND_TRIGGERS` rule triggered safety stop (`SAFETY_STOP bond-trigger inbound cmd=0x0e key=1`, `DISCONNECT ok`, exit code 3) [H]. Zero pairing attempts or link keys occurred; protected system pairing posture.
- **Step:** Owner ran `safe-write --command time` in interactive Terminal (multiple runs).
  - **Decision:** Transmitted 13-byte packed time frame in single piece (`TX piece 1/1 len=13`) [H].
  - **Decision:** Immediate watch ACK received: `cmd=0x02 key=0x01 status=1 x=0x000d x_is_frame_len=True` [H]. Confirmed invariant I-18 live (ack field x = frame length = 13); zero macOS pairing dialogs triggered; clean exit code 0.
  - **Rationale:** Strict adherence to safety checks; report updated in `targets/c900/tasks/results/LIVE-SESSION-3-2026-10-13.md`.

## 2026-10-13 Robustness pack (Asia/Saigon)
- **Decision:** one framework README with lane ownership, a branch per task (`c900/rxx`), result-file-only edits, and an integrator checklist. **Rationale:** lets weaker agents run concurrently without merge conflicts or edits to shared truth files.
- **Decision:** `tools/dexgrep.py` so static tasks work where jadx cannot be installed (as in this cloud session).
- **Decision:** R05 restored to the pack with clean specification of cmd 0x05 activity/telemetry sync and remaining field maps (keys 13, 15).

## 2026-10-13 Robustness pack integration (Asia/Saigon)
- **Step:** fast-forwarded the work branch to `feat/c900-hiwear-plus` and merged `c900/r01`..`r10`. **Rationale:** the handoff's run sheet targets `feat/c900-hiwear-plus`, but this session may push only its own branch; merging there keeps the feature branch untouched until a PR.
- **Step:** spot-checked worker `[C]` citations with `tools/dexgrep.py` before applying any doc text. **Rationale:** README section 5 integrator checklist; it caught R05's nonexistent classes.
- **Step:** applied R08 F-01..F-05 as code plus tests in `CoreTest.kt`. **Rationale:** each finding had a concrete failure path in the current core; fixes are small and local.
- **Step:** added skill `re-step-rationale`. **Rationale:** the coordinator asked for it; kept short because AGENTS.md already requires rationale in steps.md.

## 2026-10-13 Follow-up static pass (Asia/Saigon)
- **Step:** traced who displays `DayStepEntity.getDistance/getCalorie` (`dexgrep refs`, then `dump` of `HomeFragment` lambda). **Decision:** settle units from the display code; rejected: waiting for the owner screenshot. **Rationale:** the formatter is static evidence available now; the screenshot can still promote it to [H]. **Evidence:** [C] `div-float` by 1000.0f. **Revisit if:** the owner comparison disagrees.
- **Step:** `privacy_scan` frame-header exemption. **Decision:** skip runs starting in bytes 1-8 of a DF/FD frame; rejected: allowlisting each value, and skipping whole frames. **Rationale:** a header-start run has fewer than 6 payload bytes so cannot be a MAC; skipping whole frames would hide a classic MAC in a 0x0E key 1 payload. **Evidence:** [V] `test_strict_skips_runs_inside_frame_header`. **Revisit if:** a frame with a different header length is added.
- **Step:** `HealthSync` in the Kotlin core, inbound only. **Decision:** no cmd 5 request writer; rejected: adding cmd 5 key 1 to the allowlist. **Rationale:** a new write path needs review and owner approval (ground rule 7). **Revisit if:** the owner approves a history-sync request.
- **Step:** rewrote `re-step-rationale` with a when-to-write table, a **Revisit if** field and c900 examples. **Rationale:** the first version had format only; the failures seen this session (re-accepting bad claims, summaries drifting) need the check-before-acting and rejection rules.

## 2026-10-14 G4 local test run, Key 2 unit settlement, bond prompt decision (Asia/Saigon)
- **Step:** `cd client/c900-android && ~/tools/gradle/bin/gradle :core:test --rerun-tasks` and `python3 -m unittest discover -s tests`.
  **Decision:** verified both Kotlin and Python test suites on the owner's macOS host with local JDK 21 (`~/tools/jdk`) and Gradle 8.10.2; rejected: none.
  **Rationale:** Gradle build in cloud was throttled by Maven Central HTTP 429; running locally verifies all 26 Kotlin tests (`CoreTest`, `FuzzTest`, `HealthSyncTest`) and 150 Python tests cleanly before any merge.
  **Evidence:** [V] 26 Kotlin tests and 150 Python tests passed.
  **Revisit if:** Kotlin dependencies or toolchain paths change.
- **Step:** `dexgrep dump HistoryStepAdapter getView` on `work/c900-apk/com.myled.HiwearPlus.apk` (classes2.dex lines 235-297).
  **Decision:** settled cmd 5 key 2 hourly distance and calorie units as meters and calories [C]; rejected: assuming key 2 units without bytecode check [I].
  **Rationale:** the follow-up pass settled key 12 day-total units via `HomeFragment` but left key 2 as assumed [I]; `HistoryStepAdapter.getView` operates directly on `DayMinuteStepEntity` (populated by `StepUtils.getSportBy1Hour` for key 2), dividing raw int distance by 1000.0f (`const/high16 1148846080`) to format "Km" or * 0.621371 for "Miles", and dividing raw int calorie by 1000.0f for "Kcal".
  **Evidence:** [C] `HistoryStepAdapter.getView` lines 235-297.
  **Revisit if:** real device capture with non-zero hourly records shows a different conversion factor.
- **Step:** recorded owner decision on unsolicited `cmd 0x0E key 1` bond prompts in `targets/c900/CLIENT-DESIGN.md`.
  **Decision:** option (c) - never prompt the user; cache the Classic BT MAC silently and answer with protocol ACK; rejected: option (a) prompt every time, option (b) prompt once per session.
  **Rationale:** asked owner directly per LIVE-NEXT section 24 requirement; owner decided option (c) ("i want this to be automatic run while i sleep kind of thing") to prevent dialog popups during unattended background operation while sleeping.
  **Evidence:** Owner prompt response 2026-10-14.
  **Revisit if:** owner desires interactive Bluetooth Classic audio/call pairing UI in settings.

## 2026-10-14 Review of owner-machine pass (Asia/Saigon)
- **Step:** made `Session` follow the owner decision for inbound 0x0E key 1. **Decision:** cache the 6-byte classic MAC in memory and ack, no prompt; rejected: leaving code as is, also dropping the 0x0C key 19 prompt. **Rationale:** CLIENT-DESIGN and code disagreed; the decision covers 0x0E key 1 only, and 0x0C key 19 is an explicit pairing request. **Evidence:** owner decision in CLIENT-DESIGN 3.4. **Revisit if:** the owner wants classic audio pairing from the open client.

## 2026-10-14 G4 Android app shell implementation (Asia/Saigon)
- **Step:** Added `:app` module in `client/c900-android` configured with AGP 8.7.0, Kotlin 2.0.21, minSdk 26, targetSdk 35, single plain `MainActivity`, and dependency on `:core`. Configured user-space Android SDK via `local.properties`.
  **Decision:** Minimal Android SDK framework classes without Compose or external UI libraries; rejected: Jetpack Compose.
  **Rationale:** The G4 app shell goal is a headless/minimal container hosting background connection services that compiles to a debug APK without UI dependencies.
  **Evidence:** [V] `:app:assembleDebug` and `:app:testDebugUnitTest` pass.
  **Revisit if:** Full UI screens (Device, Settings, Health) are implemented in Phase 3b.
- **Step:** Implemented `PacingScheduler` enforcing single in-flight GATT operation and 20 ms piece pacing.
  **Decision:** Interval tracked from piece execution dispatch (`lastWriteAt`), scheduling subsequent writes after remaining interval; rejected: unpaced bursts or fire-and-forget.
  **Rationale:** Bluetooth controller buffers drop packets or desync when ATT pieces arrive without pacing (I-16, R08 F-05); decouples scheduling from Android Bluetooth stack for JVM unit testing.
  **Evidence:** [C] smali `const-wide/16 0x14` in send runnable; [V] `PacingSchedulerTest.testWritePiecesPaced20MsApart`.
  **Revisit if:** Real HCI capture shows different write gap on C900 hardware.
- **Step:** Added fail-closed `Gatt.isDenied(uuid)` checks across `GattLink.findCharacteristic`, `GattLink.executeOp`, and `PacingScheduler.enqueue`.
  **Decision:** Refuse and drop any read, write, or descriptor notification write targeting denied OTA/DFU UUIDs (`0xFF00`, `0x18A8`, `*dcca9e`, `5610`); rejected: allowing caller-specified GATT UUIDs.
  **Rationale:** Enforces strict OTA isolation (I-14, I-54); prevents companion client from ever touching OTA/firmware channels.
  **Evidence:** [C] Invariants I-14, I-54; [V] `PacingSchedulerTest.testDeniedUuidsAreNeverQueued`.
  **Revisit if:** Phase 4 reviewed OTA design is approved by owner.
- **Step:** Implemented `WatchService` foreground service (`connectedDevice` type) owning `Session`, `CommandQueue`, `HealthSync`, and `GattLink`.
  **Decision:** Reconnect delays set to 10000 ms on disconnect, 3000 ms on connect failure; rejected: immediate reconnect loop.
  **Rationale:** PROTOCOL section 11 and smali `BaseReconnectBlueActivity.onDisConnected` (`const-wide/16 10000`) and `reConnectBlue` (`const-wide/16 3000`). Prevents phone battery drain and Bluetooth controller lockups.
  **Evidence:** [C] smali constants 10000 ms / 3000 ms; PROTOCOL section 11.
  **Revisit if:** Real device test indicates different backoff is needed.
- **Step:** Implemented inbound 0x0E key 1 silent memory cache and 0x0C key 19 notification prompt in `WatchService`.
  **Decision:** Silent memory cache for 0x0E key 1, notification prompt with default No for 0x0C key 19; rejected: calling `createBond` or prompting on 0x0E key 1.
  **Rationale:** Owner decision 2026-10-14 in CLIENT-DESIGN 3.4 for unattended operation while sleeping; Invariant I-30 for zero spontaneous bonding.
  **Evidence:** [C] CLIENT-DESIGN 3.4; Invariant I-30.
  **Revisit if:** Owner requests interactive BT Classic audio pairing.
- **Step:** Implemented `NotificationMapper` and `DisconnectedMessageQueue`.
  **Decision:** Extended type table with Other=13; bounded FIFO dropping oldest beyond 5; zero logging of notification text; rejected: type 255 for other, unbounded queue.
  **Rationale:** Feature byte 15 bit 0x02 is set on C900 Watch Ultra (`BleDataUtils.isNewMsgPushSetting`); smali `MsgPushHelper.onAppMsgReceive` caps queue to 5 (`size > 4 -> remove(0)`); privacy hard rule forbids logging private notification content.
  **Evidence:** [C] smali `MsgPushHelper.getNewType` and `onAppMsgReceive`; [V] `NotificationMapperTest`, `DisconnectedMessageQueueTest`.
  **Revisit if:** Feature map byte 15 bit 0x02 is clear on another device family.

## 2026-10-14 G4 Android app shell review fixes (Asia/Saigon)
- **Step:** Implemented notification filtering and deduplication in `NotificationMapper` and `NotifyListener`.
  **Decision:** Default `PUSH_UNMAPPED = false` (`TYPE_IGNORE`), filter `FLAG_ONGOING_EVENT`, `FLAG_GROUP_SUMMARY`, and own package name, and deduplicate identical (package, title, body) within 2000 ms window via `NotificationDeduplicator`; rejected: forwarding unmapped apps as type 13 or forwarding ongoing notifications.
  **Rationale:** Unfiltered ongoing notifications (music progress, file downloads) fire multiple updates per second, each generating 2-3 ATT chunks that exhaust the 200-write session budget within minutes and accelerate flash wear (violating ground rule 7); vendor app only pushes "other" when explicitly toggled on (`MsgPushHelper.getShowOtherNotify` [C]) and dedupes identical text (R04).
  **Evidence:** [C] `MsgPushHelper.getShowOtherNotify` smali; [V] `NotificationFilterTest`, `NotificationMapperTest`.
  **Revisit if:** User settings allow opting into unmapped notifications or customized deduplication interval.
- **Step:** Handled terminal failures (`Session.Action.Fail`) in `GattLink` and `WatchService`.
  **Decision:** Added `onTerminalFail` callback on `GattLink.Listener`; `WatchService` sets `isFailedTerminal = true`, aborts command queue, displays "Watch not supported" user notification, and blocks all reconnect attempts until `connectDevice()` is called again; rejected: routing `Action.Fail` to `onError` with 3 s reconnect delay.
  **Rationale:** A failure action from `Session` indicates missing command service or unreviewed protocol version; reconnecting every 3 s against unknown or unsupported firmware risks unexpected device writes and battery drain.
  **Evidence:** [C] `Session.discovered` and `readResult` failure actions; [V] `ReconnectControllerTest.testTerminalFailBlocksReconnect`.
  **Revisit if:** Auto-reconnect with exponential backoff for known recoverable session errors is designed.
- **Step:** Marshaled `BluetoothGattCallback` invocations to service looper in `GattLink`.
  **Decision:** Post every `BluetoothGattCallback` callback body to `handler` (`Looper.getMainLooper()`); rejected: direct synchronous callback execution on Binder thread.
  **Rationale:** Android invokes Bluetooth callbacks on arbitrary Binder threads, while `WatchService` interacts with `Session`, `CommandQueue`, and `HealthSync` from main looper (1 s periodic tick, reconnect timer, notification sender); posting to handler guarantees thread confinement and eliminates state corruption.
  **Evidence:** [C] Android `BluetoothGattCallback` thread specification; [V] `PacingSchedulerTest`.
  **Revisit if:** Background coroutines or explicit mutex locking is introduced in core.
- **Step:** Switched timers to monotonic clock `SystemClock.elapsedRealtime()`.
  **Decision:** Passed `{ SystemClock.elapsedRealtime() }` to `CommandQueue`, `HealthSync`, and `PacingScheduler`; rejected: `System.currentTimeMillis()`.
  **Rationale:** Monotonic elapsed realtime prevents time skew from NTP adjustments, manual clock changes, or daylight savings that could prematurely trigger or starve ack timeouts (100 s), sync idle timeout (30 s), and piece pacing (20 ms).
  **Evidence:** [C] Android `SystemClock.elapsedRealtime` API specification; [V] `PacingSchedulerTest`.
  **Revisit if:** Target platform is decoupled from Android OS stubs.
- **Step:** Cleaned up permissions in `AndroidManifest.xml` and documented legacy Bluetooth rationale.
  **Decision:** Removed `RECEIVE_BOOT_COMPLETED` and `WAKE_LOCK`. Retained `android.permission.BLUETOOTH` and `android.permission.BLUETOOTH_ADMIN` with `android:maxSdkVersion="30"`; rejected: retaining unused permissions.
  **Rationale:** Neither boot completion nor wake locks were approved in R10 or used by the app shell. The legacy `BLUETOOTH` and `BLUETOOTH_ADMIN` permissions with `maxSdkVersion="30"` are necessary because the project targets `minSdk 26` (Android 8.0-11 require legacy Bluetooth permissions prior to Android 12 API 31 `BLUETOOTH_SCAN`/`BLUETOOTH_CONNECT`).
  **Evidence:** [C] Android API documentation for Bluetooth permissions across API levels 26-31.
  **Revisit if:** `minSdk` is raised to 31+.
- **Step:** Ensured immediate release of `BluetoothGatt` on disconnect or error status.
  **Decision:** Call `gatt.disconnect()`, `gatt.close()`, and null `bluetoothGatt` in `onConnectionStateChange` on any error status or `STATE_DISCONNECTED`, and call `disconnect()` on `onError`; rejected: postponing `close()` until next connect call.
  **Rationale:** Android has a strict limit on open GATT clients across processes (typically 32); failure to close on error disconnect leaks GATT resources and eventually causes status 133 / connection exhaustion.
  **Evidence:** [C] Android `BluetoothGatt.close()` documentation.
  **Revisit if:** Reconnect reuse of existing GATT instance is demonstrated on vendor stack.

## 2026-10-14 G4 drop stale GATT callbacks after reconnect (Asia/Saigon)
- **Step:** Guarded all `BluetoothGattCallback` bodies in `GattLink` against stale/replaced connections.
  **Decision:** At the top of every `handler.post` callback block, check `if (gatt !== bluetoothGatt)`; in `onConnectionStateChange`, close the stale connection via `try { gatt.close() } catch (_: SecurityException) {}` without notifying `listener.onDisconnected` or modifying scheduler state; in other callbacks, return immediately; rejected: processing callbacks without verifying connection currency.
  **Rationale:** When the service reconnects, queued or in-flight callbacks from the old connection executing on the main looper would falsely report disconnects for the new connection, abort active commands, and induce a reconnect loop; late write callbacks could also inappropriately complete new operations.
  **Evidence:** [C] Android `BluetoothGattCallback` lifecycle; [V] `GattLinkTest.testStaleDisconnectAfterReconnectDoesNotCallListenerOnDisconnected`.
  **Revisit if:** Multi-device concurrent GATT connections are introduced.

## 2026-10-14 G4 Task 2: Device picker UI and BLE scanner (Asia/Saigon)
- **Step:** Implemented `MainActivity` BLE device picker scanning for advertised name "Watch Ultra".
  **Decision:** Filter BLE advertisements to `TARGET_DEVICE_NAME = "Watch Ultra"` (FACTS section 1 [C]) using `ScanFilter`, request runtime permissions `BLUETOOTH_SCAN` and `BLUETOOTH_CONNECT` on Android 12+ without location access, list discovered devices via plain Views (`LinearLayout`, `ListView`, `Button`, `TextView`, `ProgressBar`), start `WatchService` and dispatch `connectDevice` on item selection; rejected: scanning without name filter or using Jetpack Compose/external libraries.
  **Rationale:** Ground rule: never connect to unexpected devices or firmware; R10 specifies `neverForLocation` flag; plain Views avoid library bloat.
  **Evidence:** [C] FACTS section 1 advertised name "Watch Ultra"; [V] `DevicePickerTest`.
  **Revisit if:** Support for multiple watch advertised names is added.
- **Step:** Implemented `NotificationSettings` and `SettingsActivity` with SharedPreferences persistence.
  **Decision:** Created `NotificationSettings` wrapping SharedPreferences for "push other apps" (default `false`) and per-type on/off switches (default `true` for mapped types), replaced static `PUSH_UNMAPPED` constant in `NotifyListener`, and built plain Views `SettingsActivity`; rejected: PreferenceFragment / AndroidX Preference library.
  **Rationale:** Preserves zero-dependency plain View architecture while replacing hardcoded constants with user-configurable settings; keeps unmapped apps off by default to protect the 200-write session budget and watch flash (ground rule 7, vendor `MsgPushHelper.getShowOtherNotify` [C]).
  **Evidence:** [C] `MsgPushHelper.getShowOtherNotify` smali; [V] `NotificationSettingsTest`.
  **Revisit if:** User-facing preference categories or custom app mappings are requested.
- **Step:** Implemented `StatusActivity` and `StatusSnapshot` formatting logic.
  **Decision:** Built plain Views `StatusActivity` (`ScrollView`, `LinearLayout`, `TextView`, `Button`) auto-refreshing every 1000 ms via main looper Handler, formatting connection state, battery, protocol ver, HealthSync day totals (km, kcal), and session write counter (writes / 200); decoupled pure formatting into `StatusSnapshot`; rejected: polling via background thread or binding LiveData/Flow architecture.
  **Rationale:** Main thread confinement is maintained by reading `WatchService.activeInstance` on main looper; pure `StatusSnapshot` model enables fast unit test coverage without Android UI stubs; visual feedback on the 200-write budget keeps session limits visible to the user (ground rule 7).
  **Evidence:** [C] Invariants I-10 (protocol ver), I-24 (distance/cal scaling /1000), ground rule 7 (200-write cap); [V] `StatusSnapshotTest`.
  **Revisit if:** Live data architecture (e.g. StateFlow) is required for multi-activity UI bindings.
- **Step:** Implemented end-to-end JVM consistency test `EndToEndTest`.
  **Decision:** Created `EndToEndTest` driving `Session`, `CommandQueue`, `PacingScheduler`, and `HealthSync` against a simulated peripheral (`SimWatch`) over a fake GATT link, validating connect, 4 info reads (`2a27`, `2a26`, `2a28`, `2a19`), notify enable, message transmission and protocol ACK matching, and inbound cmd 5 health sync sequence (keys 7..12..8); rejected: testing against mockito-stubbed android.bluetooth classes.
  **Rationale:** Drives exact production logic across core state machines, pacing schedulers, and queue handlers deterministically without Android framework emulation; ground rule 6 explicitly specifies this proves consistency only, not hardware truth.
  **Evidence:** [V] `EndToEndTest.testEndToEndSessionWithSimWatch`.
  **Revisit if:** Multi-chunk inbound notification reassembly or dynamic GATT MTU changes are introduced.
- **Step:** Conducted self-review audit across all `client/c900-android/app/` files and fixed thread marshaling.
  **Decision:** Audited all 21 files in `app/` against the 8 safety requirements; fixed `WatchService.sendNotification` and `WatchService.connectDevice` to marshal through `handler.post` to guarantee that calls from `NotifyListener` (OS Binder thread) touch `Session`, `CommandQueue`, and `DisconnectedMessageQueue` strictly on the main looper; verified all other items pass (zero `createBond`, fail-closed `Gatt.isDenied`, zero logging, `elapsedRealtime` clocks, manifest-only permissions, zero timer sends); rejected: allowing direct concurrent calls from service entry points.
  **Rationale:** `NotificationListenerService.onNotificationPosted` executes on a background Binder thread in Android; posting to main looper prevents multi-threaded corruption of core data structures.
  **Evidence:** [C] Android `NotificationListenerService` threading documentation; [V] `testEndToEndSessionWithSimWatch`.
  **Revisit if:** Multi-threaded synchronization primitives are added to `core`.
- **Step:** Authored `targets/c900/tasks/LIVE-APP-1.md` run sheet for initial live device evaluation.
  **Decision:** Specified strict budget (1 connect, 4 info reads, at most 3 feature writes: find, time, one message, <= 4 ATT pieces), zero pairing/bonding, explicit abort triggers, and scrubbed logging protocols for owner-attended execution; left unexecuted; rejected: executing against real hardware or leaving live session steps unscripted.
  **Rationale:** Fulfills ground rules 1, 2, and 7; hardware contact requires explicit owner presence and adherence to tight write budgets.
  **Evidence:** [C] Invariants I-18, I-21, I-35; ground rules 1, 2, 7; `targets/c900/tasks/LIVE-APP-1.md`.
  **Revisit if:** Additional feature write commands (e.g. alarm, sedentary) are added to the client allowlist.

## 2026-10-14 Review of overnight batch (Asia/Saigon)
- **Step:** added Find and Sync time buttons (`WatchService.sendFind/sendTimeSync`). **Decision:** one tap = one command, only when READY; rejected: a debug intent or automatic send on connect. **Rationale:** LIVE-APP-1 needs them and an automatic send would be a write the owner did not ask for. **Revisit if:** the live run shows the watch needs time sync on every connect.
- **Step:** LIVE-APP-1 pre-flight limits notification types to SMS. **Decision:** run-sheet step; rejected: a code-level "test mode". **Rationale:** the settings screen already does it; no new code path to review. **Revisit if:** a second live session needs other types.
## 2026-10-14 Cloud Android build (Asia/Saigon)
- **Step:** built `c900/app-shell` (822e344) in the cloud. **Decision:** machine-local Gradle init script pointing Maven Central at Google's Central mirror; rejected: editing repo build files, the Gradle plugin portal (redirects to Central, still 429). **Rationale:** keeps the repo build unchanged while removing the owner as the only build machine. **Evidence:** [V] 26 core + 23 app tests pass, APK assembles. **Revisit if:** Maven Central stops rate-limiting this environment, or the mirror host is blocked.
- **Step:** wrote the cloud Gradle setup as five steps in `docs/CLOUD-SETUP.md`, linked from skill `re-client-sim`. **Decision:** mark both with "(ReWork port candidate: ...)"; rejected: a separate list file. **Rationale:** the owner will later ask to port reusable skills to the ReWork base repo; a fixed phrase makes them findable with `grep -rn "ReWork port candidate"`. **Revisit if:** the port happens (remove the markers then).

## 2026-10-14 Batch 2 Task A1: Health record parsers in :core (Asia/Saigon)
- **Step:** implemented pure Kotlin health record decoders in `client/c900-android/core/src/main/kotlin/rewatch/c900/HealthRecords.kt` and tests in `HealthParsersTest.kt`.
  **Decision:** added individual parsers for cmd 5 keys 2 (hourly steps), 4 (heart rate), 5 (blood pressure), 9 (sleep summary), 12 (day total bounds clamp), 13 (temperature with signed tenths), 14 (SpO2), and 15 (sport sessions) using shared 2-byte `HealthDate.parse`; wrapped all parsers in non-throwing null safety; rejected: throwing exceptions on malformed input or creating Android-dependent data classes.
  **Rationale:** PROTOCOL.md §7 and C900-Q16 define strict field layouts and bounds in pure bytecode without Android framework dependencies; returning null on truncated or out-of-bounds payloads avoids crashes on unexpected BLE noise.
  **Evidence:** [C] PROTOCOL.md §7, C900-Q16, `DevBaseDataUtils.getDateBean`, `StepUtils.getSportBy1Hour`, `HrUtils.getHrDataList`, `DevBaseDataUtils.getBloodBean`, `SleepUtils.receiveTotalSleepData`, `TempUtils.getTempDataList`, `DevBaseDataUtils.getSportModeData`; [V] `HealthParsersTest` (10 unit & fuzz tests pass).
  **Revisit if:** A full-sync capture reveals multi-record payloads for key 14 or alternative field meanings for [U] mode data.

## 2026-10-14 Batch 2 Task A2: Wire parsers into HealthSync (Asia/Saigon)
- **Step:** wired all cmd 5 health record decoders into `client/c900-android/core/src/main/kotlin/rewatch/c900/HealthSync.kt` and verified via `CoreTest.collectAllRecordsAndExposeWhenDone`.
  **Decision:** aggregated incoming cmd 5 payloads per key into internal record lists during sync, and exposed an immutable `SyncedHealthData` snapshot plus convenience accessors strictly upon reaching `State.DONE`; maintained `HealthSync` as strictly inbound-only with zero outbound cmd 5 requests; rejected: exposing partial/uncommitted sync records while still `SYNCING` or adding automated pull requests.
  **Rationale:** Fulfills requirement A2 and prevents UI/storage layers from reading incomplete sync states; avoids unsolicited radio writes without explicit owner authorization.
  **Evidence:** [C] PROTOCOL.md §7.2, §11; [V] `CoreTest.collectAllRecordsAndExposeWhenDone` (37 Kotlin core unit tests pass).
  **Revisit if:** Owner approves outbound cmd 5 health record query triggers.

## 2026-10-14 Batch 2 Task A3: Local storage in :app (Asia/Saigon)
- **Step:** implemented plain SQLite storage helper in `client/c900-android/app/src/main/kotlin/rewatch/c900/app/HealthStorage.kt`, pure dedupe logic in `HealthDeduplicator.kt`, unit tests in `HealthDedupeTest.kt`, and wired persistence into `WatchService.kt`.
  **Decision:** created 8 SQLite tables with composite primary keys `(date, time)` using `CONFLICT_REPLACE` via `android.database.sqlite`; decoupled deduplication logic into pure Kotlin functions in `HealthDeduplicator` to unit-test all record types without Android emulator or Room dependencies; rejected: adding Room or external ORM libraries, or exposing any network export API.
  **Rationale:** Fulfills requirement A3; plain SQLite satisfies local persistence with zero added dependencies; pure function dedupe testing allows fast JVM test execution; composite primary keys guarantee idempotency across repeated health sync passes.
  **Evidence:** [C] PROTOCOL.md §7.2, CLIENT-DESIGN §3.5; [V] `HealthDedupeTest` (8 dedupe unit tests pass, 43 app unit tests total).
  **Revisit if:** Schema migration is needed for additional vendor record types.

