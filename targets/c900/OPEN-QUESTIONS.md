# C900 / Hiwear Plus — open questions

**Status: DRAFT — pending owner review (Phase 0).**  
Each item: why it matters, priority, evidence so far, how to answer, cost, dependencies.  
**P0** = blocks first useful contact plan · **P1** = needed soon for a solid PROTOCOL · **P2** = later · **Deferred** = implementation-only or post-hardware.

Last draft: 2026-10-13 (Asia/Saigon).

---

## Priority legend

| Priority | Meaning |
|---|---|
| P0 | Decide before or with first hardware session design |
| P1 | Answer in Phase 1 static pass if owner approves |
| P2 | Nice-to-have static / later compare |
| Deferred | Implementation or Phase 3+; do not spend Phase 1 budget |

---

## P0 — first-contact blockers (mostly hardware)

### Q1. C900 advertisement name and scan-record marker
- **Why:** Client/scanner must find the watch; app uses MAC+`12:34` or names `B0`/`H2`/`HY`.
- **Evidence:** PROTOCOL 3 [C] app rules; actual C900 advert [U].
- **How:** HW-2 read-only scan (capture adv + scan response).
- **Cost:** One approved BLE session, no writes.
- **Deps:** Owner phone/adapter + approval.

### Q2. GATT services the C900 actually exposes
- **Why:** Confirm NUS/command path vs OTA 0xFF00 / DFU 0x18A8 presence before any write plan.
- **Evidence:** App knows several UUIDs [C]; device side [U].
- **How:** HW-2 service discovery (read-only).
- **Cost:** Same session as Q1.
- **Deps:** Q1 connectable device.

### Q3. Bonding required?
- **Why:** App may `createBond` during sync; Gemini claimed none.
- **Evidence:** App has createBond path [C]; device requirement [U].
- **How:** HW-2/HW-3 observe bond state; no forced bond without approval.
- **Cost:** Read-only session.
- **Deps:** Q2.

---

## P1 — Phase 1 static (proposed)

### Q4. Remaining command-channel keys/payloads for first-contact features
- **Why:** Time/message/find are known; weather, alarms, health/sport query, settings keys, drink/sedentary still incomplete for a full PROTOCOL table.
- **Evidence:** CommandID + SettingIssuedUtils / MsgPushHelper / GeneralUtils / HealthUtils partial [C]; many keys not tabulated.
- **How:** Static — targeted read of those classes + smali for literals; tables into PROTOCOL 5.
- **Cost:** Medium (half-day agent); no LFS pull if decompiled tree already present.
- **Deps:** Bootstrap only if tree missing.

### Q5. Inbound DF payload map (finish S5)
- **Why:** Listen-only HW-3 needs to know what notifies mean.
- **Evidence:** Ack follow-ups sketched [C]; per-key DF bodies incomplete.
- **How:** Static — `NotifyWriteUtils` + `BleDataUtils` (+ related parsers).
- **Cost:** Medium.
- **Deps:** Q4 overlap OK.

### Q6. Dial `.bin` obfuscation + header trim (document + synthetic test)
- **Why:** Understand store-face pipeline; not to implement upload.
- **Evidence:** decodeInfo + getFileBuffer trim [C]; field semantics still thin.
- **How:** Static — DialDetailActivity / StringUtils; optional synthetic unit test (no vendor dial in git).
- **Cost:** Low–medium.
- **Deps:** None for docs; tests optional.

### Q7. OTA ready-reply (fun 0x81) field map and CRC edge cases
- **Why:** PROTOCOL 6 first pass may mis-state offsets; matters if Phase 4 ever happens; also prevents wrong “safe” assumptions.
- **Evidence:** OTANotifyWriteUtils parsing [C] partially documented.
- **How:** Static — smali/Java of dataHandle; document only; **no client send**.
- **Cost:** Low–medium.
- **Deps:** Owner must keep Phase 4 gated.

### Q8. Contacts sync framing (command vs OTA main=4)
- **Why:** Contacts ride OTAUtils main=4; clarify vs command-channel so nobody invents a DF opcode for it.
- **Evidence:** ContactActivity → OTAUtils(4,1) [C].
- **How:** Static — short PROTOCOL note + OPEN-QUESTIONS close.
- **Cost:** Low.
- **Deps:** None.

---

## P2 — later / optional static

### Q9. Server endpoint inventory completion
- **Why:** Know login/dial/OTA hosts; never call them from the client by default.
- **Evidence:** ~70 Retrofit endpoints sketched [C] PROTOCOL 8.
- **How:** Static — expand table (host, path, auth style); no tokens/URLs with secrets.
- **Cost:** Low–medium.
- **Deps:** None.

### Q10. HryFine opcode comparison
- **Why:** Shared `api/hry` hint; landscape wrongly assumed HryFine was the C900 app.
- **Evidence:** Partial [I]; no HryFine pin in this target.
- **How:** Only if owner supplies/pins a HryFine artifact; new SOURCES entry; optional.
- **Cost:** High (second APK + LFS or local file).
- **Deps:** Owner pin decision.

### Q11. Exact PAR container layout (native)
- **Why:** DIY watch faces; **not** needed for first contact.
- **Evidence:** `ParTool.rawToPar` [C]; bytes [U] in libabpartool.
- **How:** Native RE optional; or HW capture of a push (Phase 4).
- **Cost:** High.
- **Deps:** Phase 4 approval; prefer defer.

### Q12. Cus5610 / 0x18A8 DFU command details
- **Why:** Firmware path; dangerous.
- **Evidence:** Inventory only [C].
- **How:** Static inventory expansion **document-only**; never implement.
- **Cost:** Medium; low priority vs first contact.
- **Deps:** Keep blocked in client forever unless dedicated firmware project.

---

## Deferred — implementation-only (not Phase 1)

| ID | Topic | Why deferred |
|---|---|---|
| D1 | CLI pair / scan implementation | Phase 3; needs Q1–Q3 [H] |
| D2 | Session state machine / reconnect | Phase 3 |
| D3 | Expanding SimWatch into device model | Misleading until [H] |
| D4 | Message/time/find send helpers beyond codec | Phase 3 after HW-4+ |
| D5 | Watch-face or contact upload code | Phase 4 + design review |
| D6 | Any OTA/DFU write path in client | Forbidden without dedicated approval |
| D7 | UI / packaging / ad-free product polish | After protocol MVP |

---

## Owner checklist (Phase 0 sign-off)

- [ ] Priorities P0–P2 acceptable (edit freely)
- [ ] Phase 1 may answer: ___ (list Q numbers)
- [ ] Explicitly deferred: PAR / HryFine / Cus5610 / client features (confirm or promote)
- [ ] Bootstrap required for Phase 0? (default **no**)
- [ ] Sign-off date / notes:
