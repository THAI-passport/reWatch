# C900 / Hiwear Plus — open questions (assignable)

**Status: Phase 0 signed off 2026-10-13 for the approved Phase 1 scope (C900-Q04, Q05, Q07, Q08, Q09; Q06 optional).** All other entries stay DRAFT. Phase 1 ran 2026-10-13 (Asia/Saigon): Q04, Q06, Q07, Q08, Q09 done; Q05 partial (stop condition b, createBond conflict in FACTS). Findings: [recon-v2.md](recon-v2.md).  
Start from [recon-v2.md](recon-v2.md) (Phase 1 findings), then [recon-v1.md](recon-v1.md). Each ID is owner-free and assignable to a subagent.

**Priority means importance, not run order.** P0 items need the watch and therefore run last (after HW-0 and per-session owner approval). Recommended run order once Phase 0 is signed: Q13 (ask owner) -> Q08 -> Q04 -> Q05 -> Q07 -> Q06 -> HW-0 -> Q01 -> Q02 -> Q03.

**Who:** every `static` question can be finished by an AI alone. Every `hardware-approval` question needs a human with the watch; an AI may only prepare the run sheet and must never fabricate `[H]` results.

**Stop conditions for every question:** stop and write the result file (state `partial`) if (a) the answer needs a class not listed in Inputs and more than two extra classes, (b) a value conflicts with FACTS.md (record it there, do not pick a winner), (c) work would touch a blocked command or OTA send path beyond reading, or (d) the decompiled tree is missing and bootstrap FAILs.

Fields: **Inputs** · **Method** · **Gate** (`static` | `hardware-approval`) · **Acceptance** · **Output** · **Priority** · **Deps** · **Cost**.

---

## P0 — hardware (gate: hardware-approval)

### C900-Q01 — Advertisement name and scan-record marker
- **Why:** Scanner must find the watch; app rules may not match retail name “C900”.
- **Evidence so far:** App match MAC+`12:34` / `56:10` / name `B0|H2|HY` [C] (`BleScanActivity`); on-air C900 [U]. See recon-v1 §3.
- **Inputs:** Approved BLE adapter/phone; recon-v1; PROTOCOL §3; HW-RECON.md; HW-0 run sheet signed.
- **Method:** Read-only scan; record adv name, raw scan record hex, RSSI; no connect required if adv enough — prefer connectless first.
- **Gate:** hardware-approval (HW-2).
- **Acceptance:** Table: name(s), whether MAC+12:34 present, sample scan-record excerpt (MAC masked); FACTS/PROTOCOL updated with `[H]`.
- **Output:** `tasks/results/C900-Q01.md` (+ PROTOCOL/FACTS patches).
- **Priority:** P0 · **Deps:** HW-0; C900-Q13 (a capture may already answer this) · **Cost:** one short session.

### C900-Q02 — GATT services present on device
- **Why:** Confirm command NUS vs OTA 0xFF00 / 0x18A8 before any write plan.
- **Evidence so far:** App UUID table [C] recon-v1 §3; device [U].
- **Inputs:** Q01 connectable target; PROTOCOL §2.
- **Method:** Connect read-only; service discovery; list UUIDs; optional 0x180A reads; **no writes**, no OTA chars write.
- **Gate:** hardware-approval (HW-2).
- **Acceptance:** Service/characteristic list vs PROTOCOL §2; note missing/extra; `[H]` tags.
- **Output:** `tasks/results/C900-Q02.md`.
- **Priority:** P0 · **Deps:** C900-Q01 · **Cost:** same session as Q01 OK.

### C900-Q03 — Bonding behaviour
- **Why:** Affects first-contact procedure.
- **Evidence so far:** App may createBond during sync [C] (`BleDataUtils`); device ask [U].
- **Inputs:** Q02 connection; PROTOCOL §3, §7.
- **Method:** Observe bond state on connect + during listen (HW-3); do not force bond unless approved.
- **Gate:** hardware-approval.
- **Acceptance:** Statement: bond required / optional / never seen; `[H]`.
- **Output:** `tasks/results/C900-Q03.md`.
- **Priority:** P0 · **Deps:** C900-Q02 · **Cost:** low.

---

## P1 — static (gate: static; Phase 1 only after Phase 0 sign-off)

### C900-Q04 — Command-channel key/payload tables (first-contact set) (**closed: done 2026-10-13**, see tasks/results)
- **Why:** PROTOCOL §5 lists keys incompletely for weather/alarms/health/settings.
- **Evidence so far:** CommandID + partial SettingIssuedUtils/MsgPushHelper [C]; recon-v1 §5.
- **Inputs:** recon-v1; decompiled tree (bootstrap if missing); class list in RECON-HIWEAR-APK Phase 1.
- **Method:** Smali check of the 100 s ack-timeout literal first. Then targeted `rg` + read `CommandID`, `SettingIssuedUtils`, `MsgPushHelper`, `GeneralUtils`, `HealthUtils` / sport helpers; smali for literals.
- **Gate:** static.
- **Acceptance:** PROTOCOL §5 tables for: time (done—verify), message, find, camera, alarms, step goal, profile, notification switches, settings query 0x09; each row cmd/key/payload layout/tag/source method. No client feature code. Rows not reached stay `[U]` with the method name to read next.
- **Output:** `tasks/results/C900-Q04.md` + PROTOCOL patch.
- **Priority:** P1 · **Deps:** Phase 0 approval · **Cost:** medium.

### C900-Q05 — Inbound DF payload map (**closed partial 2026-10-13; remainder = C900-Q14**)
- **Why:** Listen-only (HW-3) needs decode map.
- **Evidence so far:** S5 first pass; recon-v1 §5; PROTOCOL §7 sketch.
- **Inputs:** Probe `NotifyWriteUtils`, `BleDataUtils`, health parsers.
- **Method:** Static trace notify → dispatch → parsers; table cmd/key → fields.
- **Gate:** static.
- **Acceptance:** PROTOCOL §7 table covering health/sport (cmd 5), settings replies, find-phone, camera shutter, battery path; `[C]` sources named.
- **Output:** `tasks/results/C900-Q05.md` + PROTOCOL patch.
- **Priority:** P1 · **Deps:** Phase 0; overlaps Q04 · **Cost:** medium.

### C900-Q06 — Dial `.bin` decode + header trim (**closed: done 2026-10-13**, see tasks/results)
- **Why:** Document store-face pipeline; not to implement upload.
- **Evidence so far:** decodeInfo + getFileBuffer [C]; recon-v1 §6.
- **Inputs:** `DialDetailActivity`, `utils/StringUtils`; synthetic bytes only in tests.
- **Method:** Static; optional unittest with synthetic obfuscated string (no vendor dial in git).
- **Gate:** static.
- **Acceptance:** PROTOCOL §6.1 field offsets for trim rule; token seeds noted; test optional but green if added.
- **Output:** `tasks/results/C900-Q06.md` (+ test if any).
- **Priority:** P1 · **Deps:** Phase 0 · **Cost:** low–medium.

### C900-Q07 — OTA ready-reply (0x81) + CRC edge cases (docs only) (**closed: done 2026-10-13**, see tasks/results)
- **Why:** Tighten PROTOCOL §6.3; prevent false “safe to send” assumptions. Most fields are already listed in PROTOCOL §6.3 (first pass); this question is a **smali verification** of field widths, the 0x31 poly and the default/init interval conflict (300 vs 500), not new research.
- **Evidence so far:** First-pass D5/D6 [C]; recon-v1 §6.
- **Inputs:** `OTANotifyWriteUtils`, `OTAUtils`, `CommandUtils` (+ smali for 0x31).
- **Method:** Static field map for fun 0x81 payload; document group vs file CRC; **no send code**.
- **Gate:** static.
- **Acceptance:** PROTOCOL §6.3 byte map + CRC note with `[C]`; explicit “client must not implement”.
- **Output:** `tasks/results/C900-Q07.md`.
- **Priority:** P1 · **Deps:** Phase 0 · **Cost:** low–medium.

### C900-Q08 — Contacts path confirmation (OTA main=4) (**closed: done 2026-10-13**, see tasks/results)
- **Why:** Stop anyone inventing a DF opcode for contacts.
- **Evidence so far:** ContactActivity → OTAUtils(4,1) [C].
- **Inputs:** `ContactActivity`, `MainActivity` sync call sites.
- **Method:** Short static confirm; PROTOCOL cross-link.
- **Gate:** static.
- **Acceptance:** PROTOCOL note + this question closed or marked verified `[C]`.
- **Output:** `tasks/results/C900-Q08.md`.
- **Priority:** P1 · **Deps:** Phase 0 · **Cost:** low.

---

## P2 — static optional

### C900-Q09 — Server endpoint inventory expansion (**closed: done 2026-10-13**, see tasks/results)
- **Why:** Know hosts/paths; never call from client by default.
- **Inputs:** Retrofit API interfaces under decompiled sources.
- **Method:** Static table host/path/auth-style; scrub secrets.
- **Gate:** static.
- **Acceptance:** PROTOCOL §8 table expanded; no tokens/signed URLs.
- **Output:** `tasks/results/C900-Q09.md`.
- **Priority:** P2 · **Cost:** low–medium.

### C900-Q10 — HryFine opcode compare (optional)
- **Why:** Shared `api/hry` hint only.
- **Inputs:** Owner-pinned HryFine artifact + new SOURCES entry (do not download unpinned).
- **Method:** Static compare CommandID/framing if artifact provided.
- **Gate:** static (+ owner pin).
- **Acceptance:** Short diff table or “not pinned — skipped”.
- **Output:** `tasks/results/C900-Q10.md`.
- **Priority:** P2 · **Cost:** high if pinned.

### C900-Q11 — PAR container layout (native)
- **Why:** DIY faces only; not first contact.
- **Inputs:** `ParTool`, `libabpartool` (if extracted); or defer to capture.
- **Method:** Native RE optional; else leave [U].
- **Gate:** static (or hardware-approval capture in Phase 4).
- **Acceptance:** Layout doc `[C]`/`[U]` explicit; no upload client.
- **Output:** `tasks/results/C900-Q11.md`.
- **Priority:** P2 · **Cost:** high.

### C900-Q12 — Cus5610 inventory (docs only)
- **Why:** Firmware path awareness; never implement.
- **Inputs:** `Cus5610CommandUtils`, `Cus5610OTAUtils`.
- **Method:** Static fun-code table; mark NEVER USE.
- **Gate:** static.
- **Acceptance:** PROTOCOL §6.4 inventory table; client still has no path.
- **Output:** `tasks/results/C900-Q12.md`.
- **Priority:** P2 · **Cost:** medium.

---

### C900-Q13 — Existing owner capture (HW-1) as software input
- **Why:** AGENTS.md: captures the owner already has count as software and come before probing. One HCI snoop of Hiwear Plus pairing + time sync could settle Q01-Q03 and the MTU/ack-timeout values with no new watch contact.
- **Evidence so far:** Owner answer 2026-10-13: No capture yet (2026-10-13). Q01-Q03 stay live tasks. Later option: the owner can record an Android HCI snoop log of Hiwear Plus pairing and time sync on their own phone. It is cheap and owner-run, and worth doing before HW-0. It is the owner's choice; the AI does not request it.
- **Inputs:** Owner answer; `re-capture-ingestion` skill; `tools/btcap.py`.
- **Method:** Ask the owner whether a btsnoop exists. If yes: scrub (mask MAC), ingest with btcap, map handles. If no: record "none" and keep Q01-Q03 as live tasks. The AI never asks the owner to install or run the vendor app on its behalf; capturing is the owner's own choice.
- **Gate:** static once supplied (owner action to supply).
- **Acceptance:** Either "no capture" recorded, or a scrubbed summary with `[H]` rows promoted into FACTS/PROTOCOL. No raw capture committed if it has personal data.
- **Output:** `tasks/results/C900-Q13.md`.
- **Priority:** P0 (cheapest P0) · **Deps:** owner reply · **Cost:** low.

---

## Phase 1b (APPROVED by owner 2026-10-13)

Owner 2026-10-13: no live test until necessary. So the next phase is **Phase 1b: static only**. Hardware (Phase 2) stays parked; HW-0 is written as a document but nothing is run.

### C900-Q14 — Inbound map remainder (approved Phase 1b)
- **Why:** HW-3 listen-only and any future capture need a complete decode table; Q05 stopped early.
- **Who:** AI alone. **Gate:** static.
- **Inputs:** `tasks/results/C900-Q05.md` (mapped part, do not redo); decompiled tree via `bash tools/cloud_bootstrap.sh` (expect `PASS`; on FAIL stop and log).
- **Method, in order (one class each, smali for every literal):**
  1. `HealthUtils.analusis`: cmd 5 key -> record type and field offsets (steps, sleep, HR, BP, SpO2, temperature).
  2. `UserInfoAndRemindUtils.parsingUseInfoAndRemind`: cmd 9 reply layout.
  3. `BleDataUtils.handleWatchFaceInfo`: cmd 0x0F keys 2/5/6/8/9 fields.
  4. `BleDataUtils.setSettingSuccess`: FD-ack cmd/key -> follow-up table, including the exact createBond condition.
  5. `MainActivity$4.run`: what schedules it and when it calls createBond.
  6. Camera shutter (`BleInfoCallback.callDeviceContro`, `DeviceContro` enum) and the 0x2A19 battery handler.
  7. `NotifyWriteUtils.readFeatures` smali: is b25 0x80 really shared by `isShowHrAutoTest` and `isShowDnd`?
- **Acceptance:** each step has a row in a table (cmd, key, offset, width, endianness, meaning, tag, source method) or an explicit `[U]` with why; createBond conditions written into FACTS §4 and PROTOCOL §3; PROTOCOL §7 updated; no client code.
- **Stop conditions:** the shared ones above; also stop if a step needs more than two classes not named here.
- **Output:** `tasks/results/C900-Q14.md` + PROTOCOL/FACTS patches + steps.md.
- **Priority:** P1 · **Deps:** none · **Cost:** medium (one bootstrap, one session).

### C900-Q15 — HW-0 run sheet, written only (approved Phase 1b; document only)
- **Why:** when hardware becomes necessary, the first session must be ready, read-only and budgeted. Writing it touches nothing.
- **Who:** AI writes; owner approves before any use. **Gate:** static (document).
- **Inputs:** `tasks/HW-RECON.md`, `re-hardware-recon` skill, recon-v2 §3, PROTOCOL §2-3, C900-Q14 result if done.
- **Method:** fill a run sheet for HW-1 (owner HCI snoop, optional), HW-2 (passive scan, then connect + discovery + reads of 0x2A19, 0x2A26-0x2A28; **no writes, no notify enable on OTA services, never touch 0xFF00 / 0x18A8 / ...DCCA9E**) and HW-3 (enable notify on ...0003 only; listen; no writes). Budget per session: connects, reads, max duration, abort triggers (unexpected bond prompt, disconnect loop, any OTA UI on the watch). MAC masking rule. Expected values per step from PROTOCOL with tags.
- **Acceptance:** one file a human can follow without this conversation; every step says expected result and what to do on deviation; zero write steps.
- **Output:** `tasks/HW-0-RUNSHEET.md` (marked DRAFT, not approved).
- **Priority:** P1 · **Deps:** Q14 preferred · **Cost:** low.

### Q13 (unchanged, optional)
An owner-made Android HCI snoop of Hiwear Plus pairing is still the cheapest way to settle Q01-Q03 without our own contact. Owner's choice; not required.

### Still parked
Q01-Q03 (need the watch; only when the owner says live work is necessary), Q10 (needs pin), Q11, Q12, D01-D07.

---

## Deferred — implementation (not assignable in Phase 1)

| ID | Topic | Output when unblocked | Gate |
|---|---|---|---|
| C900-D01 | CLI scan/pair | client/ + tests | hardware-approval + Phase 3 |
| C900-D02 | Session/reconnect | client/ | Phase 3 |
| C900-D03 | Rich SimWatch device model | client/ | after [H] |
| C900-D04 | Send helpers beyond codec | client/ | after HW-4+ |
| C900-D05 | Face/contact upload | client/ — design review | Phase 4 |
| C900-D06 | OTA/DFU write path | forbidden by default | dedicated approval |
| C900-D07 | Product UI / packaging | later | after protocol MVP |

---

## Owner Phase 1b checklist (signed 2026-10-13)

- [x] Run C900-Q14 (static)
- [x] Write C900-Q15 run sheet (document only, zero writes, not executed)
- [x] Hardware stays parked until you say it is necessary
- [x] Sign-off: owner approved Phase 1b, 2026-10-13 (Asia/Saigon). Also: write an owner guide for an Android HCI snoop capture (docs/guides/HCI-CAPTURE-ANDROID.md).

## Owner Phase 0 checklist (signed 2026-10-13)

- [x] Priorities OK
- [x] Phase 1 APPROVED: C900-Q04, Q05, Q07, Q08; Q06 optional
- [x] Q13: No capture yet (2026-10-13). Later option: the owner can record an Android HCI snoop log of Hiwear Plus pairing and time sync on their own phone. It is cheap and owner-run, and worth doing before HW-0. It is the owner's choice; the AI does not request it.
- [x] Q09 APPROVED for Phase 1 (static inventory only, no server calls); Q12 PARKED (OTA/DFU risk, not needed now)
- [x] Deferred D01–D07 and Q11 stay deferred; Q12 parked
- [x] Sign-off: 2026-10-13 (Asia/Saigon), owner sign-off delegated to the requesting agent by the owner. Rationale: the approved items are static, document-only and needed for listen-only and first-contact planning; Q12 touches the firmware path with no near-term use; Q13 needs a fact only the owner has.
