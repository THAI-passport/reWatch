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
