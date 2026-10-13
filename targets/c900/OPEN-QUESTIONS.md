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
- **Owner guide:** `docs/guides/HCI-CAPTURE-ANDROID.md` (how to record and hand over an Android HCI snoop log).
- **Why:** AGENTS.md: captures the owner already has count as software and come before probing. One HCI snoop of Hiwear Plus pairing + time sync could settle Q01-Q03 and the MTU/ack-timeout values with no new watch contact.
- **Evidence so far:** Owner answer 2026-10-13: No capture yet (2026-10-13). Q01-Q03 stay live tasks. Later option: the owner can record an Android HCI snoop log of Hiwear Plus pairing and time sync on their own phone. It is cheap and owner-run, and worth doing before HW-0. It is the owner's choice; the AI does not request it. How-to: `docs/guides/HCI-CAPTURE-ANDROID.md`.
- **Inputs:** Owner answer; `re-capture-ingestion` skill; `tools/btcap.py`.
- **Method:** Ask the owner whether a btsnoop exists. If yes: scrub (mask MAC), ingest with btcap, map handles. If no: record "none" and keep Q01-Q03 as live tasks. The AI never asks the owner to install or run the vendor app on its behalf; capturing is the owner's own choice.
- **Gate:** static once supplied (owner action to supply).
- **Acceptance:** Either "no capture" recorded, or a scrubbed summary with `[H]` rows promoted into FACTS/PROTOCOL. No raw capture committed if it has personal data.
- **Output:** `tasks/results/C900-Q13.md`.
- **Priority:** P0 (cheapest P0) · **Deps:** owner reply · **Cost:** low.

---

## Phase 1b (APPROVED by owner 2026-10-13)

Owner 2026-10-13: no live test until necessary. So the next phase is **Phase 1b: static only**. Hardware (Phase 2) stays parked; HW-0 is written as a document but nothing is run.

### C900-Q14 — Inbound map remainder (approved Phase 1b) (**closed 2026-10-13: steps 2-7 done; step 1 remainder = C900-Q16**)
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

### C900-Q15 — HW-0 run sheet, written only (approved Phase 1b; document only) (**closed 2026-10-13: DRAFT run sheet written; revised in REVIEW-PHASE1B**)
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
Q01-Q03 (need the watch; first try the capture route Q13 -> Q19; live only when the owner says it is necessary), Q10 (needs pin), Q11, Q12, D01-D07.

---

## Phase 1c (DRAFT, pending owner sign-off)

Plan and comparison: [NEXT-STEPS.md](NEXT-STEPS.md). Gates now include `capture` (needs a capture file the owner supplied; the AI never asks for one to be made on its behalf).

### C900-Q16 — cmd 5 health field maps (APPROVED Phase 1c 2026-10-13)
- **Why:** Q14 step 1 stopped after the key map; a capture or listen session cannot be decoded without field layouts.
- **Who:** AI alone. **Gate:** static.
- **Inputs:** `tasks/results/C900-Q14.md` step 1 (key -> decoder table, do not redo); decompiled tree (`bash tools/cloud_bootstrap.sh`, expect `PASS`; FAIL -> stop, log in LOG.md).
- **Method (one class per step, smali for every offset and shift):** `StepUtils.getSportBy1Hour` and `getTotalStepData` (keys 2, 12); `HrUtils.getHrDataList` (4); `DevBaseDataUtils.getBloodBean`, `getDateBean`, `getSportModeData` (5, 14 date, 15); `SleepUtils.receiveTotalSleepData` (9); `TempUtils.getTempDataList` (13).
- **Acceptance:** for each of keys 2, 4, 5, 9, 12, 13, 15 a table of payload offset, width, endianness, scale/unit, meaning, tag, source method; record repeat size for lists; one worked synthetic example per key in the result (bytes made up, labelled synthetic); PROTOCOL §7 updated. Rows not reached stay `[U]` with the method to read next.
- **Stop:** shared stop conditions; the five classes above count as named.
- **Output:** `tasks/results/C900-Q16.md` + PROTOCOL patch + steps.md.
- **Priority:** P1 · **Deps:** none · **Cost:** medium (one bootstrap ~105 MB LFS, one session).

### C900-Q17 — notify_log.py OTA-safe subscribe (APPROVED Phase 1c 2026-10-13, tool change)
- **Why:** `tools/notify_log.py` subscribes to every notifiable characteristic (`main_async` loop over `client.services`), which would enable notify on 0xFF00 / 0x18A8 / `...DCCA9E` OTA characteristics. HW-0 forbids that.
- **Who:** AI alone. **Gate:** static (code change; needs owner approval of Phase 1c because it edits a tool).
- **Inputs:** `tools/notify_log.py`, `tests/test_notify_log.py`, HW-0-RUNSHEET §0.
- **Method:** add `--only UUID` (repeatable; when given, subscribe to those only) and a default deny list (`--deny`, prefilled with services 0xFF00, 0x18A8 and UUIDs ending `dcca9e`, case-insensitive) that is applied even without `--only`; print the subscribed list before listening; refuse to start if a denied UUID would be subscribed. No other behaviour change.
- **Acceptance:** unit tests with a fake client cover: default run skips OTA chars; `--only` subscribes exactly one; denied UUID in `--only` exits non-zero. `python3 -m unittest discover -s tests` and `python3 tools/rw.py lint` green; README/tool docstring updated; FIXES.md entry moved to Fixed.
- **Output:** code + tests + `tasks/results/C900-Q17.md`.
- **Priority:** P1 · **Deps:** none · **Cost:** low; no LFS.

### C900-Q18 — Capture decoder prep and fixture dry run (APPROVED Phase 1c 2026-10-13, tool change)
- **Why:** when a capture arrives it should be parsed in one pass. `tools/btcap.py` lists ATT writes/notifies per handle but does not reassemble or decode DF/FD frames (checked 2026-10-13 against `tests/fixtures/synthetic_gatt.btsnoop`: works, output is raw hex).
- **Who:** AI alone. **Gate:** static (code change).
- **Inputs:** `tools/btcap.py --json`, PROTOCOL §4 and §7, `client/c900/frames.py` (read only), C900-Q04/Q05/Q14 tables.
- **Method:** a small stdlib script (for example `tools/c900_decode.py`) that reads btcap JSON, keeps one handle pair (write `...0002`, notify `...0003`, chosen by flag), reassembles DF frames to `len + 4`, checks the sum, labels cmd/key from a table built from PROTOCOL (names only, no new claims), flags any write with a blocked cmd, and prints 0x2A27/0x2A28/0x2A19 reads with the feature bits Q14 cares about (b1 0x80, b15 0x40, b18 0x20, b25 0x80). Build a **synthetic** btsnoop fixture with made-up DF frames (bind, accept 0x0C/8, time sync + ack, 0x0C/19) and run the decoder on it as the dry run. Mask any address the tool prints.
- **Acceptance:** tests green on the synthetic fixture; output shows each frame decoded and a summary block (version byte seen, feature bits, bond triggers seen yes/no, blocked cmds seen yes/no). No vendor data in the fixture.
- **Output:** script + fixture + tests + `tasks/results/C900-Q18.md`.
- **Priority:** P1 · **Deps:** none (Q16 improves cmd 5 labels later) · **Cost:** low-medium; no LFS.

### C900-Q19 — Ingest the owner capture (gate: capture)
- **Why:** cheapest path to `[H]` for Q01-Q03, the version byte, feature bits and the watch's ack bytes, with no contact by us.
- **Who:** AI alone once the owner supplies the file. **Gate:** capture.
- **Inputs:** `captures/btsnoop_hci.log` (git-ignored) + owner step-time notes and phone model; skill `re-capture-ingestion`; Q18 decoder (or `btcap.py` alone if Q18 is not done).
- **Method:** follow NEXT-STEPS.md §4 (decision tree). Map handles to UUIDs from the capture's discovery; decode; compare every value with PROTOCOL/FACTS.
- **Acceptance:** `tasks/results/C900-Q19.md` with masked excerpts only (no notification text, no full MAC, no profile values); each settled item promoted to `[H]` in FACTS/PROTOCOL with the capture as source; each conflict as a FACTS row; Q01-Q03 states updated. Raw capture never committed.
- **Stop:** capture contains a watch-face, OTA or contacts transfer (owner did a forbidden step) -> record only that it happened, do not decode the file payload; capture lacks the pairing/connect part -> record what is missing and ask the owner.
- **Output:** `tasks/results/C900-Q19.md` + FACTS/PROTOCOL patches.
- **Priority:** P0 · **Deps:** C900-Q13 (owner) · **Cost:** low; no LFS.

### Owner Live Session 1 Pre-flight Decision (2026-10-13)
- **Live work necessity:** Owner approved: "live work is necessary" for scope = LIVE-SESSION-1 only (2026-10-13 Asia/Saigon).
- **Classic pairing resolution:** Owner chose **Option A** from `LIVE-PREFLIGHT-REVIEW.md` §4:
  - Action: Owner disconnects `Watch Ultra` in macOS System Settings -> Bluetooth (leaving pairing keys intact, Classic link idle).
  - Risk waiver: Waives the strict "never paired" no-go checklist item with risk noted in writing (dual-mode chip LE cross-transport key derivation risk acknowledged).
  - Probe posture: Read-only first contact (scan + inspect, 0 GATT data writes) via owner's interactive Terminal session using per-Mac CoreBluetooth BLE UUID.

### Owner Phase 1c checklist (SIGNED 2026-10-13)
- [x] Approve C900-Q16 (static, one bootstrap)
- [x] Approve C900-Q17 (tool fix; edits `tools/notify_log.py`)
- [x] Approve C900-Q18 (decoder + synthetic fixture)
- [x] Q13: will you record a capture with `docs/guides/HCI-CAPTURE-ANDROID.md`? **later** (2026-10-13)
- [x] Confirm HW-0 stays parked until you say live work is necessary
- [x] Confirm Phase 3 (client) and Phase 4 (OTA, faces) stay deferred
- [x] Sign-off: 2026-10-13 (Asia/Saigon), owner approval relayed by the requesting agent. Run order Q17 -> Q18 -> Q16.

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
