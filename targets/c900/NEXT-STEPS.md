# C900 / Hiwear Plus: next steps (DRAFT)

**Status: DRAFT, pending owner sign-off.** Revised 2026-10-13 after Phase 1c (REVIEW-PHASE1C). Written 2026-10-13 (Asia/Saigon) in REVIEW-PHASE1B. Nothing here is approved to run. Owner rule in force: no live test until necessary.

Every step below assumes [INVARIANTS.md](INVARIANTS.md).

## 1. Where we are
Static work has mapped framing, command tables, the inbound map, bond triggers and the OTA path [C] (recon-v2.md). What is left falls in three groups:
- **Static, still open:** none that code reading can settle; cmd 9 bytes 9-13 and distance/calorie units need data [U].
- **Only the watch knows:** advertised name and scan record (Q01), services present (Q02), whether it asks to bond (Q03), `PROTOCOL_VERSION` from 0x2A27, feature bytes from 0x2A28 (b1 0x80, b15 0x40, b18 0x20, b25 0x80), the watch's own ack bytes 6-7, which keys it acks, and whether the jadx index arithmetic for cmd 9 tags 4/7/9/11 holds.
- **Tooling gaps:** `notify_log.py` would subscribe to OTA characteristics; nothing decodes DF/FD frames out of a capture.

## 2. Paths compared

| | Path 1: owner HCI capture (Q13 -> Q19) | Path 2: HW-0 read-only session | Path 3: remaining static (Q16) | Path 4: capture tooling (Q17, Q18) |
|---|---|---|---|---|
| Goal | Real vendor-app traffic with the C900, decoded | Our own read-only look at the watch | Finish cmd 5 field maps | Be ready to parse in one pass; make HW-3 safe |
| Prereqs | Owner's Android phone, watch already bound, guide `docs/guides/HCI-CAPTURE-ANDROID.md`; owner chooses to do it | HW-0-RUNSHEET approved per session; Linux/macOS + adapter + bleak; owner present; Q17 done | Phase 1c sign-off; bootstrap PASS | Phase 1c sign-off |
| Steps | Owner: enable snoop, reconnect app, time sync, one test message, find watch, battery, bug report, copy `btsnoop_hci.log` to `captures/`. AI: `python tools/btcap.py captures/btsnoop_hci.log --json captures/c.json`, then the Q18 decoder (or tshark `-Y btatt`), then decision tree §4 | Run sheet HW-2.1-2.4, HW-3.1-3.2 exactly | One class per step as in Q16 | Q17 tool fix + tests; Q18 decoder + synthetic fixture + dry run |
| Risk | Privacy (notifications, profile, location, other devices); owner might tap an update or unbind (guide forbids) | Bond prompt, the phone stealing the link, accidental OTA subscribe (mitigated by Q17 + snippet), disconnect loops | Low; jadx/smali disagreement | Low; tool changes reviewed by tests |
| Cost: time | Owner ~20 min; AI ~1 short session | Owner ~30 min + setup; AI prep ~0 (sheet exists) | AI 1 session | AI 1 session total |
| Cost: LFS / AI budget | 0 LFS; small | 0 LFS; small | ~105 MB LFS (one bootstrap); medium | 0 LFS; low |
| Answers | Q01 (name, raw adv bytes from the snoop), Q02 (discovery), Q03 (pair pop-up, 0x0C/19, 0x0E/1, time ack + b15), version byte, all feature bytes, watch ack bytes, key ack set, cmd 9 real layout, cmd 5 real records, OTA none (forbidden in guide) | Q01, Q02, version, features, battery; Q03 only if the watch volunteers a trigger; no ack bytes (we write nothing) | cmd 5 layouts [C] only | Nothing new by itself; makes Paths 1 and 2 faster and safer |
| Success | `C900-Q19.md` with `[H]` rows promoted; Q01-Q03 closed or narrowed | Run-sheet result file, all steps ticked or aborted with reason | `C900-Q16.md` with every key tabled or `[U]` with reason | Tests green; decoder prints summary on the synthetic fixture |
| Stop | Capture shows a forbidden transfer (face/OTA/contacts) -> note only, do not decode payload; pairing part missing -> ask owner | Any abort trigger in HW-0 §2; budget hit | Shared stop conditions | Any change beyond the named tools |

## 3. Recommended order and why (revised 2026-10-13 after Phase 1c)
Paths 3 and 4 are **done** (C900-Q16, Q17, Q18; reviewed in REVIEW-PHASE1C). Static work is effectively exhausted: what is left ([U] distance/calorie units, cmd 9 bytes 9-13, extra sport fields) needs real data, not more code reading.
1. **Path 1 now: owner capture (Q13 -> Q19).** Only the owner can start it. Before recording, the owner checks the list below. After the file arrives the AI runs, in order:
   1. `python tools/c900_decode.py captures/btsnoop_hci.log > captures/decoded.txt` (feed the capture file, not btcap JSON: the JSON path has no ATT reads, so 0x2A27/0x2A28/0x2A19 would be missing).
   2. If no frames appear on the default UUIDs: `python tools/btcap.py captures/btsnoop_hci.log` to map handles, then rerun the decoder with `--write-handle` / `--notify-handle`.
   3. Walk the decision tree (section 4); write `tasks/results/C900-Q19.md` with masked excerpts only. Never commit `captures/`.
2. **Path 2 (HW-0) last**, only for what the capture leaves open, after the owner says live work is necessary.
3. If the owner decides not to capture: stop and wait. HW-0 is not a substitute without the owner's explicit "live work is necessary".

### Before you record (owner checklist)
- [ ] Watch already bound to Hiwear Plus (do not unbind to re-bind)
- [ ] Snoop log set to **Enabled**, not Filtered; Bluetooth toggled off and on after
- [ ] Placeholder profile values and location off, if you prefer privacy
- [ ] Plan: reconnect, time sync, one test message, find watch, battery; note phone times
- [ ] No faces, updates, contacts, unbind or reset; decline any update prompt
- [ ] Send only `btsnoop_hci.log` (and any `.last` files), privately

### Decoder limits (REVIEW-PHASE1C)
- A message whose first piece is missing cannot be resynced; it shows as stray chunks or a bad sum, never as a wrong decode.
- Labels are names from PROTOCOL; an unlabelled cmd/key is a finding, not a decoder bug.
- Decoded values become `[H]` only once written to the result file with the capture as source.

## 4. Decision tree for the capture (Q19)
1. **Find the watch connection.** No LE connection to a device that discovers `6E400001-...DCCA9F`: capture is wrong or filtered -> ask the owner for model/Android version and whether "Enabled" (not Filtered) was set; stop.
2. **Services (Q02).** Compare discovery with PROTOCOL §2. Missing NUS -> stop, FACTS conflict, the C900 may use another transport; no HW-0 until reviewed. Extra unknown services -> record, list only.
3. **Version byte.** Read 0x2A27 value and the `ver` byte of app writes (0-based index 5, right after cmd at index 4; I-10 numbering note). Equal to 1 -> `[H]`, codec default holds. Not 1 -> FACTS row; D-version (codec takes version as input) becomes a Phase 3 must.
4. **Feature map.** 0x2A28 byte 0 = 0xAA -> decode bits. Not 0xAA -> look for cmd 0x19 reply instead.
5. **Bonding (Q03).**
   - SMP pairing request in the log, or 0x0C/19, 0x0E/1, or b15 0x40 with a following bond -> watch-side bonding `[H]`; HW-0 must expect a pairing prompt: change the abort rule to "cancel and stop" (already), and plan a separately approved bonded session if needed.
   - None of these -> "no bond seen in this capture" `[H]` for this firmware; HW-0 can run without a pairing agent.
6. **Acks.** Record bytes 6-7 of watch FD acks and which cmd 2 keys get acks -> replace SimWatch's `[I]` ack in FACTS (code fix waits for Phase 3).
7. **Name and scan record (Q01).** If advertising reports are in the log, record the name and whether MAC + `12 34` appear; if the phone connected from cache without scanning, Q01 stays open for HW-2.1.
8. **Unexpected frames.** Any DF cmd/key not in PROTOCOL §7 -> raw row in the result, `[H]` unknown meaning; never replay.
9. **Forbidden content seen** (face, OTA, contacts transfer) -> note it happened and the size only.
After the tree: if Q01-Q03 are all settled, HW-0 shrinks to an optional confirmation; if not, HW-0 runs only the steps for what is open.

## 4b. Capture vs live session: which comes first, and what each removes (DRAFT, DEEP-PASS-1)
Live sessions are planned in `tasks/LIVE-SESSION-1.md` (read-only, session 1; writes are session 2 in its section 9). The rule is: never spend a live step on a question a capture already answered.

| Situation | Do | Skip |
|---|---|---|
| Capture arrives before any live session | Run section 4 on it, then fill LIVE-SESSION-1 section 0 from the capture | Every session-1 row the capture settled |
| Capture settles Q01 name, Q02 services, version byte, feature map, and Q03 | Session 1 is **skipped**; consider session 2 only if the capture lacks acks for find/time/message | Session 1 entirely |
| Capture settles all of the above **and** shows watch acks for cmd 2 keys 1, 11, 18 | Sessions 1 and 2 both skipped; ack bytes become `[H]` from the capture | All live work until Phase 3 needs it |
| Capture lacks raw advertising (phone connected from cache) | Q01 scan-record question stays open; session 1 step 3 only, or a Mac PacketLogger trace during step 3 (optional, owner installs Apple's Additional Tools; trace format readable by Wireshark [I]) | Session 1 step 4 if services/version/features came from the capture |
| Capture shows SMP pairing or a bond trigger (0x0C/19, 0x0E/1, b15 0x40 + bond) | Session 1 still allowed (read-only) but the pairing dialog is now expected: abort trigger 1 stays "Cancel and stop"; a bonded session is a separate approval | Nothing extra |
| Capture shows `ver` != 1 | Session 2 is blocked (the probe refuses to write unless 0x2A27 major is 1); codec must take the version as input first (D-version) | Session 2 |
| Capture missing NUS (`...DCCA9F`) | Stop; FACTS conflict; no live session until reviewed | Both sessions |
| Session 1 runs first (no capture) | After it, the capture is still worth asking for: it is the only source of the bind sequence (cmd 3 then 0x0C/8), ack bytes for many keys, and health records, without us writing anything | Capture steps already settled by session 1 (name, services, version, features) need no second look |
| Owner declines both | Stop and wait (owner rule, I-51) | - |

Order of preference: capture first (no watch contact by us), then session 1 only for gaps, then session 2 only for ack evidence the capture lacks.

## 5. Budget summary
| Step | LFS | AI sessions | Owner time | Watch contact by us |
|---|---|---|---|---|
| Q17 + Q18 (done) | 0 | 1 | 0 | none |
| Q16 (done) | ~105 MB | 1 | 0 | none |
| Q13 + Q19 | 0 | 1 short | ~20 min | none |
| HW-0 / LIVE-SESSION-1 (if needed) | 0 | 0-1 | ~30 min | 2 connects, 7 reads each, 1 CCCD each, 0 writes |
| LIVE-SESSION-2 (separate approval) | 0 | 0-1 | ~20 min | 3 connects, 1 read each, 1-2 writes each (4 total) |

## 6. Must be true before Phase 3 (client) starts
- Q01 and Q02 `[H]` (scan rule and services) and Q03 at least narrowed to `[H]` "bond seen / not seen".
- `PROTOCOL_VERSION` value on the C900 `[H]`, and the codec plan takes it as input (D-version).
- Watch ack bytes `[H]` (or the codec ignores them, documented).
- For every command the MVP sends (time, message, find, battery read): payload `[C]` and seen on the wire `[H]` (capture counts), plus a write-cost note (flash wear) per ground rule 7.
- `notify_log.py` fixed (Q17); blocklist still `{0x01,0x04,0x06,0x07,0x0D,0x13}` with a test.
- Owner approval of a Phase 3 scope written in PLAN.md.
Phase 3 (client) and Phase 4 (OTA, watch faces, contacts push, Cus5610) stay **deferred**.

## 7. After LIVE-SESSION-1 (2026-10-13, DRAFT, pending owner sign-off)
Settled [H]: Q01, Q02, feature map, idle behaviour. Open: real ver byte, FF10/FF12 purpose, bond behaviour after bind/time ack, ack bytes.

| Order | Step | Who | Needs | Settles |
|---|---|---|---|---|
| 1 | **S-20 static:** smali of `NotifyWriteUtils.onRead` 0x2A27 parse and `PROTOCOL_VERSION` store (int-to-byte?), plus every place that reads 2A27/2A26 strings | AI | one rebuild (justified: [I] blocks session 2) | ver byte 0x10 vs other [C] |
| 2 | **S-21 static:** smali grep for `ff10`, `fff1`, `ff12`, `ff13`, `ff14` (and 16-bit forms) to identify the two unknown services | AI | same rebuild | FF10/FF12 purpose [C] or "not in app" |
| 3 | **Owner capture** (NEXT-STEPS sections 3-4): the single best next live-ish step; shows the real ver byte, bind sequence, ack bytes, whether the watch bonds after time sync | owner | Android phone, ~20 min | ver [H], acks [H], Q03 after bind [H] |
| 4 | Codec: `frames.build` takes ver as a parameter (default unchanged) with tests; probe passes `version_byte(major)` | AI | S-20 result or capture | unblocks session 2 |
| 5 | Session 2 (`find` only first; `time` last because b15 0x40 makes it the app's bond trigger) | owner | new approval | ack bytes [H] |

Do not run session 2 before step 4. Do not add bind (cmd 3) to the probe.

Update 2026-10-13: step 3 done (owner capture, C900-Q19 incl. section 7); step 4 done (`frames.build(..., ver=)`, `C900_VER = 0x10`, SimWatch ack x = frame length, probe sends the 0x2A27-derived ver). Steps 1-2 (static) are now optional: the wire settled the ver byte; S-21 (FF10/FF12) still open. Next live step: session 2, `find` first, after written approval.
