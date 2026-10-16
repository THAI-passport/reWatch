# C900 / Hiwear Plus plan

**Status:** Phase 1 and Phase 1b done (approved 2026-10-13, Asia/Saigon). **Phase 1c Q16-Q18 APPROVED 2026-10-13; Q13 capture later (Q19 waits for it); HW-0 parked; Phase 3/4 deferred.** Next-step comparison: [NEXT-STEPS.md](NEXT-STEPS.md). Findings: [recon-v2.md](recon-v2.md).

Last draft: 2026-10-13 (Asia/Saigon). Findings: [recon-v2.md](recon-v2.md) (current), [recon-v1.md](recon-v1.md) (first snapshot).

---

## 1. Revised goal

**Primary:** Understand the Hiwear Plus ↔ C900 protocol well enough to design an **open-source, ad-free replacement client**, with a clear map of what is known, what is dangerous, and what still needs evidence.

**Not the main goal right now:** Implementing client features, shipping CLI UX, or uploading watch faces. Existing `client/c900/` work is **deferred** (see section 5).

**Success for the next review gate:** Owner-approved `PLAN.md` + prioritized `OPEN-QUESTIONS.md`, then a bounded Phase 1 static pass that answers only the approved questions.

## 2. What is already done (do not redo)

| Area | State | Where |
|---|---|---|
| App identity + pin (2.0.1 / 31) + REPO_COPY LFS | done | SOURCES.md, resources/ |
| DF/FD framing, checksum, len, MTU/chunking | [C] | PROTOCOL 4 |
| CommandID table + dangerous ids | [C] | PROTOCOL 5, FACTS 4 |
| Time sync packing (-0x7d0) | [C] smali | PROTOCOL 5, results/S2 |
| Scan filter rules (app side) | [C] | PROTOCOL 3 |
| OTA D5/D6 path for dial/paper/contact (document only) | [C] first pass | PROTOCOL 6, results/S4 |
| Server endpoint sketch | first pass | PROTOCOL 8 |
| Inbound ack-driven sync sketch | first pass | PROTOCOL 7, results/S5 |
| Gemini disputes logged | done | FACTS 2 |
| Cloud bootstrap for agents | done | docs/CLOUD-SETUP.md |

## 3. Phases and gates

| Phase | Name | Owner gate | AI may |
|---|---|---|---|
| **0** | Plan review | **You are here.** Sign off on PLAN + OPEN-QUESTIONS | Read docs; light `rg` to sanity-check claims; edit PLAN/OPEN-QUESTIONS; STOP |
| **1** | Bounded static deepen | After owner approves Phase 0 question set | Decompile/smali only for approved questions; update PROTOCOL/FACTS; no client feature work |
| **2** | First-contact hardware | Per-session approval (HW-0…) | Read-only scan/listen; then single approved writes (time/message/find) |
| **3** | Client MVP (deferred) | Separate approval after Phase 2 evidence | Pair, time, notify, battery in CLI; still no OTA/faces |
| **4** | Watch faces / rich media | Reviewed design + approval | Only after OTA path design review; never ad-hoc |

Run order: Phase 1 (static) before Phase 2 (hardware) even though hardware questions are labelled P0; P0 means "most important", not "first". Phase 2 also needs the HW-0 run sheet approved, should come after an owner capture if one is possible (Q13, still "no capture yet" 2026-10-13), and is parked until the owner says live work is necessary.

Map to TARGET.md gates: G0–G2 done; G3 continues in Phase 1; **G4 Client deferred**; G5 after HW-2+.

## 4. Risks

| Risk | Mitigation |
|---|---|
| Wrong opcode sent to watch (unbind/factory/OTA) | Blocklist in codec; Phase 3+ only after [H] confirmation; never send 0x01/04/06/07/0D/13 |
| LFS bandwidth burn (~105 MB/pull, ~102 pulls/month Free) | `git lfs pull -I` one path; CI without `lfs:true`; Phase 0 often skips bootstrap |
| Jadx constant substitution | Smali for every numeric that matters (already hit on -0x7d0) |
| Scope creep into OTA/faces | Faces and Cus5610 stay document-only until Phase 4 |
| Cloud agent redoes settled work | Phase 0 deliverable is the plan; token-saving class list for Phase 1 only |
| Owner statements tagged `[owner]` read as `[C]` | `[owner]` is not an AGENTS.md tag; weigh as `[W]` until code or hardware confirms |
| A capture the owner already has is overlooked | Ask first (C900-Q13); captures are software and avoid live probing |
| First-pass `[C]` values from jadx (100 s timeout, OTA interval 300/500) | Smali check in Q04/Q07 before they are used in any run sheet |
| Implementation before understanding | Client marked deferred; Phase 0 forbids new client code |

## 5. Deferred: client / implementation

- `client/c900/frames.py` and tests stay as a **codec sketch** (opcodes + blocklist already aligned with CommandID). No new features, scanners, or session code until Phase 3 is approved.
- Do not expand the simulator into a device model.
- Do not wire OTAUtils / PAR / dial push into any client path.

## 6. Phase 1 (done 2026-10-13)

- Ran 2026-10-13 with the approved set C900-Q04, Q05, Q07, Q08, Q09, Q06 (Q12 parked). Budget: one bootstrap, one session; stop and commit when a question hits its stop condition.
- PAR native layout, HryFine compare and any OTA send design stay deferred.

## 6b. Phase 1b (APPROVED by owner 2026-10-13)

Owner 2026-10-13: no live test until necessary. Phase 1b is static only: C900-Q14 (inbound remainder, createBond conditions) and C900-Q15 (HW-0 run sheet as a document, zero writes). Phase 2 stays parked until the owner says hardware is necessary; then it starts read-only (HW-1 optional capture, HW-2, HW-3) and needs per-session approval. Bonding decision (2026-10-13): app-side createBond is [C] (FACTS §4); device side stays [U].

## 6c. Phase 1c (APPROVED 2026-10-13 for Q16-Q18; run order Q17 -> Q18 -> Q16)

Static and owner-capture work only; details and rationale in [NEXT-STEPS.md](NEXT-STEPS.md).
1. C900-Q16: cmd 5 field maps (static).
2. C900-Q17: notify_log.py safety fix (tool; DRAFT, needs approval because it edits code).
3. C900-Q18: DF/FD decoder over btcap JSON + synthetic fixture dry run (tool; DRAFT).
4. C900-Q13 -> Q19: owner capture, then ingestion (gate: capture).
5. HW-0 (Q01-Q03) only for what the capture leaves open, and only when the owner says live work is necessary.

## 7. Entry criteria for Phase 3 (client)
See NEXT-STEPS.md §6. Phase 3 and Phase 4 stay deferred.

## 8. Stop rule for every agent
After the scoped pass: commit on the feature branch, then STOP and report for owner sign-off. Never start the next phase on your own.

## 9. Phase 3 (APPROVED 2026-10-13)
Android Kotlin. 3a core done in `client/c900-android/core` (codec, reader, allowlisted commands, queue, session; tests against shared vectors). Next: app shell on a machine with Google Maven; then 3b (bind decision, health sync). Bind stays out until decided.
