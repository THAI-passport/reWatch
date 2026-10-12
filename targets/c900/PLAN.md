# C900 / Hiwear Plus plan

**Status: DRAFT — pending owner review (Phase 0).**  
Do not treat as approved work orders. Deeper decompile (Phase 1) waits for owner sign-off on this file and `OPEN-QUESTIONS.md`.

Last draft: 2026-10-13 (Asia/Saigon). Author: Grok Bot from current PROTOCOL/FACTS/LOG/STATUS.

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

Map to TARGET.md gates: G0–G2 done; G3 continues in Phase 1; **G4 Client deferred**; G5 after HW-2+.

## 4. Risks

| Risk | Mitigation |
|---|---|
| Wrong opcode sent to watch (unbind/factory/OTA) | Blocklist in codec; Phase 3+ only after [H] confirmation; never send 0x01/04/06/07/0D/13 |
| LFS bandwidth burn (~105 MB/pull, ~102 pulls/month Free) | `git lfs pull -I` one path; CI without `lfs:true`; Phase 0 often skips bootstrap |
| Jadx constant substitution | Smali for every numeric that matters (already hit on -0x7d0) |
| Scope creep into OTA/faces | Faces and Cus5610 stay document-only until Phase 4 |
| Cloud agent redoes settled work | Phase 0 deliverable is the plan; token-saving class list for Phase 1 only |
| Implementation before understanding | Client marked deferred; Phase 0 forbids new client code |

## 5. Deferred: client / implementation

- `client/c900/frames.py` and tests stay as a **codec sketch** (opcodes + blocklist already aligned with CommandID). No new features, scanners, or session code until Phase 3 is approved.
- Do not expand the simulator into a device model.
- Do not wire OTAUtils / PAR / dial push into any client path.

## 6. Proposed Phase 1 scope (subject to owner edit)

Only questions marked **P0/P1** and method **static** in `OPEN-QUESTIONS.md` after owner review. Expected themes (draft):

- Finish command-channel key/payload tables for first-contact features (weather/alarms/health/contacts **payloads** as docs, not client).
- Finish inbound DF inventory needed for listen-only.
- Dial `.bin` header trim fields (synthetic fixture OK).
- Explicitly **defer** PAR native layout, HryFine full compare, and any OTA send design unless owner promotes them.

## 7. Stop condition for Phase 0 agents

After updating PLAN.md / OPEN-QUESTIONS.md (or confirming the drafts): commit on a feature branch if asked, then **STOP and report for owner sign-off**. Do not start Phase 1.
