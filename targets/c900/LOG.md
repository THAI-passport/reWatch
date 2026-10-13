# Problem log: C900 watch

Append every pitfall, newest last. Entry: date, gate, problem, cause, solution (or Status: Unsolved plus what was tried).

---

## 2026-10-12 G1 blocked: artifact not reachable
- Evidence: APK mirror and release hosts are blocked from the cloud sandbox (recorded in the next-pass prompt, same date); no lookup made this pass.
- Cause: environment network policy.
- Fix: open. Needs the owner to supply the XAPK for `--local-file`, or the host added to the allowed domains.

## 2026-10-13 G0 duplicate target layout removed
- Evidence: `targets/t900-c900/` duplicated `targets/c900/` and `targets/t900/` (same task pack, overlapping PROTOCOL and FACTS).
- Decision: keep `targets/c900` for the C900 and `targets/t900` for the T900. The combined folder's files are kept verbatim under `sources/legacy-t900-c900-*.md` with a superseded banner; useful C900 content (frame layout, ack layout, OTA hazard) was re-checked against the app in this pass and lives in PROTOCOL.md with its new tags. `client/t900-c900/` stays as built-ahead, unverified code.

## 2026-10-13 G1 companion app was wrong
- Evidence: owner statement that the C900 uses Hiwear Plus; earlier docs assumed HryFine or HiWatch Pro from a third-party write-up.
- Fix: acquired `com.myled.HiwearPlus` 2.0.1 from APKPure (the 2026-10-12 host block no longer applied), pinned in SOURCES.md, earlier claims annotated in FACTS.md section 3. The old block entry above is closed.

## 2026-10-13 G1 floating URL
- Evidence: APKPure only offers a `version=latest` link; the redirect target is a signed CDN URL (not recorded).
- Fix: open. Owner to keep the exact file (COPY_LOCATION). A later download will likely give another hash: make a new pinned entry, never edit this one.

## 2026-10-13 G2 jadx exit 3
- Evidence: rebuild_analysis finished with jadx exit 3 (some methods not decompiled), heap capped at 3 GiB on a shared box with about 3 GiB free.
- Fix: normal; read smali for any method that matters.

## 2026-10-13 G2 third-party document wrong on opcodes
- Evidence: the Gemini document (sources/gemini-hiwear-re.md) gives the right header and checksum but wrong opcodes; two of them would unbind the watch (0x04) or start a factory test (0x07).
- Cause: opcodes guessed or copied from another app; untagged as such.
- Fix: FACTS.md section 2 lists each dispute; client opcodes must come from the [C] table only.

## 2026-10-13 G1 owner-approved repo copy (Git LFS)
- Evidence: owner instructed to zip the exact Hiwear Plus 2.0.1 XAPK into `resources/c900/hiwear-plus-2.0.1.xapk.zip` and pin it; zip 104797741 bytes, SHA-256 `800662003d57aa272e5f829908c4c7671d1118ac4ed564242a5edcd4ca8e570e`; inner XAPK unchanged `5fa761a4...8952`.
- Cause: floating APKPure URL and cloud-agent rebuild needs a local file; prior rule forbade committing artifacts.
- Fix: AGENTS.md ground rule 3 exception (exact path + REPO_COPY + LFS); `.gitattributes` tracks `resources/**/*.zip`; `rebuild_analysis.py` acquires from REPO_COPY after --local-file / existing artifact; `rw.py lint` rejects undeclared files under resources/. Solved.

## 2026-10-13 G3 time offset smali confirmation
- Evidence: jadx printed `BaseResp.CODE_ERROR_PARAMS` (-2000) in `settingSysTime`; smali shows `add-int/lit16 v2, v2, -0x7d0`.
- Cause: jadx constant substitution (same class of pitfall as reBeamBox guard 300 vs 800).
- Fix: trust smali for numeric literals; record -0x7d0 in PROTOCOL/FACTS; implement `frames.time_payload`. Solved.

## 2026-10-13 G3 OTA / watch-face framing (static)
- Evidence: `CommandUtils` / `OTAUtils` / `OTANotifyWriteUtils` / `DialDetailActivity` / `WatchFaceEditActivity` / `ParTool.rawToPar`.
- Cause: needed for PROTOCOL completeness; client must not send.
- Fix: PROTOCOL section 6 documents D5/D6 framing, CRC poly 0x31, dial.bin obfuscated Base64, PAR path. PAR container bytes remain [U] (native). No client OTA path. Solved for documentation.

## 2026-10-13 LFS bandwidth exposure (docs check)
- Evidence: GitHub docs — Free plan includes 10 GiB LFS storage and 10 GiB LFS bandwidth per month; downloads (including public clones and Actions with LFS) count against the **repository owner**. Archive is 104797741 bytes (~0.098 GiB) so about **102** full downloads fit in the monthly bandwidth quota. Overage: with budget $0 or no payment method, usage is blocked (not auto-charged); with payment method and budget deleted/raised, overages bill. CI currently omits `lfs: true` (checkout default false). Could not read live usage: `gh` token lacks billing/`user` scope; no settings changed.
- Fix: document in RECON task; keep CI without LFS fetch; agents should `git lfs pull -I` only the one path. Open for owner to confirm budget UI if desired.

## 2026-10-13 Decisions from recon-v1
- Evidence: consolidated in `targets/c900/recon-v1.md` from PROTOCOL/FACTS/S-tasks.
- Decisions (finding → action): (1) Bluetrum not Jieli → deprioritise Jieli skills for this target. (2) Face/contact/paper via OTAUtils → treat as OTA-class, defer Phase 4. (3) Dangerous CommandIDs → keep BLOCKED_CMDS. (4) Incomplete [H] → defer client features (G4). (5) Cloud rebuild need → keep one LFS REPO_COPY; CI no lfs:true. (6) Scope risk → Phase 0 plan gate before Phase 1 decompile. (7) Identity → c900 = Hiwear Plus only. (8) Gemini → framing OK, opcodes not authoritative.
- Status: Recorded; PLAN/OPEN-QUESTIONS remain DRAFT pending owner review.

## 2026-10-13 Phase 1 C900-Q08 contacts path (static)
- Evidence: `ContactActivity.saveAsFile`, `MainActivity$6` (BroadcastReceiver), `CommandUtils.smali`, `NotifyWriteUtils.readFeatures`, `BleDataUtils.handleMountBTInfo`.
- Problem: risk that a contacts DF opcode gets invented; jadx `(byte) 4` needed a smali check.
- Fix: smali `const/4 0x4` / `0x1` before both `OTAUtils.<init>` call sites; app-wide smali search shows no other main=4 site. Solved. Side find: `isSyncContact` is write-only (MD5 mismatch does not auto-sync).

## 2026-10-13 Phase 1 C900-Q04 command keys (static)
- Evidence: `SettingIssuedUtils`, `GeneralUtils`, `SportIssuedUtil`, `IssuedUtil`, `MsgPushHelper`, `NotifyWriteUtils` (jadx + smali).
- Problem 1: jadx replaced byte literals with unrelated same-valued constant names (`CommandID.COMMAND_ID_GET_FUNTION`, `CommandID.CHATGPT_ID`, `SettingIssuedUtils.KEY_SETTING_SET_LANGUAGE`, `BaseResp.CODE_ERROR_PARAMS`). Cause: jadx constant inlining by value. Fix: read the `const/16` before each `getSendByte` in smali. Solved; one real mislabel found (0x1A/21 is exit find-phone).
- Problem 2: register value at the NAK call site looked ambiguous (two `const/4 v11` in the method). Cause: smali file order is not control-flow order. Fix: followed the `if-ne` jump target from the sum check. Solved (x=3).
- Problem 3: `p0` reused as cmd register in some builders, so a regex on `v` registers missed the cmd. Fix: also match `const/16 p0`. Solved.

## 2026-10-13 Phase 1 C900-Q05 inbound map (static, partial)
- Evidence: `NotifyWriteUtils.dataHandle`, `BleDataUtils.setDeviceContro`, `readFeatures`, smali search for `BluetoothDevice;->createBond`.
- Problem: app-code `createBond` sites (3) contradict FACTS §2 / PROTOCOL §3 "no createBond in app code". Likely cause: the earlier pass searched jadx output of a narrower class set. Fix: none chosen; recorded as a conflict in FACTS and PROTOCOL §3 per stop condition (b). **Unsolved** pending review.
- Done before the stop: top-level dispatch for 14 cmds, device-control keys (find phone, camera, bind accept/refuse, media, bond), feature bit map.

## 2026-10-13 Phase 1 C900-Q07 OTA 0x81 / CRC (static, docs only)
- Evidence: `OTANotifyWriteUtils` (`<init>`, `dataHandle`, send runnable, `onWrite`), `OTAUtils.sendData/startOTA`, `CommandUtils`.
- Problem: PROTOCOL said interval "default 300 if 0; field init is 500" and recon flagged it as a conflict. Cause: jadx printed the init as `CropImageView.DEFAULT_IMAGE_TO_CROP_BOUNDS_ANIM_DURATION` (value 500); nobody had checked whether the field is read. Fix: smali shows both literals are real and the field is never used for timing. Solved.
- No send code written; client unchanged.

## 2026-10-13 Phase 1 C900-Q09 server inventory (static)
- Evidence: `network/request/Request.java`, `network/Urls.java`, `network/sse/SSEManager.java`, `utils/SignUtils.java`, `function/dial/activity/DialDetailActivity.java`.
- Problem: risk of copying secrets (signing key literal, speech SDK credential fields) into the repo. Fix: every grep piped through a scrubber that masks key/token/sign values and long tokens; recorded algorithm shape and field names only; scanned the result file with the same scrubber before commit (no matches). Solved.
- No network calls, DNS lookups or downloads.

## 2026-10-13 Phase 1 C900-Q06 dial decode/trim (static, docs only)
- Evidence: `StringUtils.decodeInfo/decodeInfoToBytes/md5Encode32`, `Base64Utils`, `DialDetailActivity.getFileBuffer`, `OwnerDialDetailActivity`, `HexUtil.byte2IntLR`.
- Problem: jadx printed the `/` replacement as `FileUriModel.SCHEME`. Fix: smali `const-string "/"`. Solved.
- Problem: name `byte2IntLR` suggests little-endian. Fix: read the body; it is big-endian over argument order, and callers pass bytes reversed. Solved.
- Optional test skipped: would only test a re-implementation against itself.

## 2026-10-13 negative search on jadx output was wrong (createBond)
- Evidence: earlier [C] "no createBond in app code"; smali shows 3 app-code call sites (C900-Q05).
- Cause: claim based on a search of jadx output; jadx output can hide or rename calls, and a negative result was tagged [C].
- Fix: row retired (FACTS §4). Rule: negative claims ("X never called") must be checked in smali before tagging [C].

## 2026-10-13 Phase 1b C900-Q14 inbound remainder (static)
- Evidence: `HealthUtils.analusis`, `UserInfoAndRemindUtils`, `BleDataUtils.handleWatchFaceInfo/setSettingSuccess`, `MainActivity$4`, `DeviceContro`, `NotifyWriteUtils.onRead/readFeatures` (jadx + smali).
- Problem: step 1 field maps sit in five parser classes not named in the step. Fix: stopped per the step stop rule; key map and inline SpO2 recorded, parsers listed. Partial.
- Problem: grep of readFeatures smali showed the b25 flags several times (default branches). Fix: read the window after the `0x1a` length check and traced the mask register back to `const/16 v4, 0x80`. Solved.

## 2026-10-13 Phase 1b C900-Q15 HW-0 run sheet (document only)
- Evidence: HW-RECON.md, re-hardware-recon skill, recon-v2 §3, PROTOCOL §2-3, C900-Q14.
- Problem: `tools/notify_log.py` subscribes to every notifiable characteristic, which would include the OTA notify characteristics. Fix: sheet forbids it for HW-3 and gives a one-UUID snippet; no tool code changed. Solved for the sheet.

## 2026-10-13 notify_log.py would subscribe to OTA characteristics
- Evidence: `tools/notify_log.py` main_async loops over all services and calls start_notify on every notify/indicate characteristic.
- Cause: generic tool written before the c900 OTA services were known.
- Fix: open. DRAFT task C900-Q17; HW-0 uses a single-UUID snippet until then. Also listed in FIXES.md Open.

## 2026-10-13 Phase 1c C900-Q17 notify_log.py OTA-safe subscribe
- Evidence: tools/notify_log.py, tests/test_notify_log.py.
- Problem: the tool enabled notify on every notifiable characteristic, OTA included (I-50). Fix: default deny list by characteristic and by service, `--only`, `--deny`, exit 2 on a denied `--only`, plan printed first; 6 new tests. Solved.

## 2026-10-13 Phase 1c C900-Q18 capture decoder
- Evidence: tools/btcap.py, PROTOCOL §4/§5/§7, client/c900/frames.py (read only).
- Problem: btcap.py lists only writes and notifies, so 0x2A27/0x2A28/0x2A19 reads were invisible. Fix: the decoder pairs ATT read request/response from the capture itself; btcap.py unchanged. Solved.
- Problem: the Phase 1b `*.btsnoop` ignore rule would hide new fixtures. Fix: `!tests/fixtures/*.btsnoop`. Solved.

## 2026-10-13 Phase 1c C900-Q16 cmd 5 field maps (static)
- Evidence: StepUtils, HrUtils, DevBaseDataUtils (getDateBean, getBloodBean, getSportModeData), SleepUtils.receiveTotalSleepData, TempUtils (jadx + smali); helper classes HexUtil, DevDateBean (two, within the stop rule).
- Problem: jadx showed `JCameraView.MEDIA_QUALITY_FUNNY` as the calorie clamp in getSportBy1Hour. Fix: smali `const v11, 0x61a80` = 400000; INVARIANTS I-24 extended. Solved.
- Problem: the health date packing looks like the time-sync packing but is different. Fix: new INVARIANTS I-36 and FACTS row. Solved.

## 2026-10-13 decoder printed personal payloads
- Evidence: `tools/c900_decode.py` hid only cmd 2 key 18; keys 17 (caller), 36 (user name), 4 (profile) and 0x1A 23/24 (location) printed as hex.
- Cause: privacy list built from the message-push case only.
- Fix: PRIVATE table + test (REVIEW-PHASE1C).

## 2026-10-13 Probe tool
- Built `tools/c900_probe.py` for owner Mac (bleak 3.0.2, hashed requirements-probe.txt).
- Modes: scan, inspect (CCCD-only write), safe-write (allowlist + dual approval).
- Hard safety in code: allowlist, BLOCKED_CMDS, OTA UUID refuse, no bonding, bond-trigger abort, caps, sanitized device strings, logs to captures/ masked.
- Tests: `tests/test_c900_probe.py` (fake bleak). Docs: PROBE-GUIDE.md, PROBE-SECURITY.md, PROMPT-GEMINI-PROBE-REVIEW.md.

## 2026-10-13 Adversarial probe review and hardening
- Evidence: `REVIEW-PROBE-SECURITY.md`, `tools/c900_probe.py`, `tests/test_c900_probe.py`.
- Problem: `_require_command_layout` OTA lookalike check had impossible `and` condition (`cu.endswith("0002") and cu.endswith(OTA_SERVICE_SUFFIX)`) and did not verify parent service was not OTA. Fix: check `is_ota_svc and cu == WRITE_UUID` and `cu.startswith("6e400002") and cu.endswith(OTA_SERVICE_SUFFIX)`. Solved.
- Problem: `is_ota_uuid` missed custom 128-bit Bluetrum 5610 UUIDs. Fix: added `"5610" in u` and fixed 32-bit UUID extraction. Solved.
- Problem: `mode_safe_write` omitted pairing check during wait loop. Fix: stored `paired_before` and added active `is_paired` check in wait loop. Solved.
- Problem: leading noise byte in `on_notify` locked buffer and blinded bond-trigger aborts. Fix: drop non-header leading bytes until `0xDF`/`0xFD` and validate `9 <= total <= 1024`. Solved.
- Problem: `redact_line` leaked personal data if literal "payload" keyword was absent. Fix: redact caller, location, message push without requiring keyword. Solved.
- Problem: write cap pre-check had `pass` allowing mid-frame abort. Fix: atomic pre-check before piece 1. Solved.
- Tests: 6 new unit tests in `tests/test_c900_probe.py` (23 total, all passing). Solved.

## 2026-10-13 Independent verify of Gemini probe hardening (c724066)
- Evidence: `git diff 8793cc6..c724066` (6 files only: probe, tests, REVIEW, FIXES, LOG, steps).
- Checked: `"5610" in u` does **not** match command UUIDs `...dcca9f` / DI / battery (regression test added). Resync drops leading noise then parses real DF/FD (including split acks); does not skip frames under 1024 B. Redaction only fires on message-push/caller/location keywords; protocol RX/ACK/TX/features lines unchanged. Write cap is atomic (`writes + len(pieces) > MAX` refuses before piece 1). `--address`/`--name` mutually exclusive. No new imports/deps. REVIEW doc treated as untrusted: no instruction injection (subprocess only in non-findings).
- Fix applied here: removed unused `_UUID_FULL` regex Gemini left behind; added regression tests (command UUIDs vs 5610, resync preserves frames, redaction keeps protocol fields, multi-piece write-cap math); documented 5610 rule on I-54.

## 2026-10-13 DEEP-PASS-1 second probe review (independent of Gemini)
- Problem: pairing detection in `tools/c900_probe.py` could never fire on real hardware. Evidence: pinned bleak 3.0.2 wheel has no `BleakClient.is_paired`; CoreBluetooth `pair()` raises NotImplementedError (macOS auto-pairs on encrypted reads). Cause: tests used a fake client with the attribute, so Gemini's safe-write fix passed. Fix: `pair_state()` returns None when unavailable, probe logs it, LIVE-SESSION-1 makes the macOS pairing dialog an owner abort trigger. Solved (code); residual risk depends on the owner.
- Problem: writes/subscribe by UUID string; notify UUID under an OTA service not refused. Fix: `command_chars()` binds to objects in `6e400001-...dcca9f`, exactly one each. Solved.
- Problem: probe sends `ver` = 1 regardless of 0x2A27 (I-10). Fix: safe-write refuses unless 0x2A27 major is 1. Solved.
- Problem: scan log stored third-party device names and full manufacturer data (PROTOCOL section 3: the C900 record may hold its MAC); inspect logged 0x2A25 (serial) in clear; target address in error text unmasked on macOS. Fix: candidate-only names, masked manufacturer bytes, 0x2A25 redacted, `add_secret`. Solved.
- Problem: stale ack accepted, no inbound flood cap, `--log-dir` anywhere, logs could overwrite, C1/bidi characters passed `sanitize`, unbounded time args, back-to-back write-without-response pieces. Fixes in DEEP-PASS-1 A.1 #6-#12. Solved.
- Problem: test fake returned empty bytes for every Device Information read (matched short UUIDs only), so reads were never tested. Fix: fake resolves full base UUIDs. Solved.
- Problem: "byte 4" for the version byte (I-10, FACTS, NEXT-STEPS) vs "cmd at byte 4" (PROTOCOL 7.1). Cause: mixed numbering. Fix: numbering note on I-10 (0-based index 5), NEXT-STEPS step 3 corrected; decoder already used index 5. Solved (docs).
- Open: Q01 raw scan record is not visible through bleak on macOS; needs a capture or PacketLogger (owner, optional).

## 2026-10-13 Live Bluetooth pre-flight, dual-profile discovery, and TCC sandbox state
- Evidence: `system_profiler SPBluetoothDataType`, `targets/c900/tasks/results/INCIDENT-2026-10-13-LIVE-BLUETOOTH-PREFLIGHT.md`.
- Finding: owner connected watch via macOS System Settings (`Connected: Watch Ultra`, services `0x800039 <HFP AVRCP A2DP HID ACL>`). This is Classic Bluetooth (BR/EDR) audio, not the BLE GATT command interface (`6E400001-...`). Bluetrum/JieLi clone watches feature dual-profile architecture; GATT telemetry requires BLE connection.
- Problem: automated BLE scan from background IDE agent hangs on CoreBluetooth dispatch. Cause: macOS TCC sandbox (`CBManager.authorization() == 0`). Non-interactive subshells cannot display interactive TCC Bluetooth prompts.
- Resolution: verified all 44 unit tests pass in `.venv-probe` with pinned hashes; documented findings and anti-RE trap evaluation in `INCIDENT-2026-10-13-LIVE-BLUETOOTH-PREFLIGHT.md`. Live probe commands remain marked `[human]` for owner execution in interactive macOS Terminal. Solved (docs / preflight).

## 2026-10-13 Pre-flight review (follow-up to the incident file)
- Problem: incident file committed the Mac controller's full Bluetooth address and the watch Classic OUI. Fix: masked in the file; still in history at 3d1b298 (owner decides on rewrite). Solved (file), open (history).
- Problem: the Mac is paired/connected to the watch over Classic, which fails LIVE-SESSION-1 go/no-go. Fix: owner chose Option A (disconnect in macOS Bluetooth settings, keep keys, waive no-go item with risk noted in OPEN-QUESTIONS.md). Solved.
- Problem: probe hangs instead of failing when the shell lacks macOS Bluetooth permission. Open: FIXES.
- Problem: incident text repeated a Jieli claim contrary to I-02 and overstated sanitize. Fix: corrections in LIVE-PREFLIGHT-REVIEW section 3.

## 2026-10-13 Live Session 1 (first contact on real hardware)
- Evidence: `captures/c900-probe-scan-20261013-133720.log`, `captures/c900-probe-inspect-20261013-133934.log`, `targets/c900/tasks/results/LIVE-SESSION-1-2026-10-13.md`.
- Findings:
  - Q01 settled [H]: Advertised name `'Watch Ultra'`, mfg data `314c:<6 masked MAC bytes>1234` (company 0x314C, watch MAC followed by marker `12 34`).
  - Q02 settled [H]: Command service `6e400001-b5a3-f393-e0a9-e50e24dcca9f` (`0002` write, `0003` notify), Battery `0x180F`, Device Info `0x180A`, and 3 OTA services (`0xFF00`, `0xFF10`, `0xFF12`).
  - Feature map settled [H]: `0xAA` marker, len 27, hex `aacfe081dff6fc3800000000000010e64108cf1400000000000000` (`isBLE3=True`, `isSupportPair=True`).
  - Q03 settled [H]: Zero unsolicited frames during 30 s listen; no pairing prompts triggered.
- Problem: `0x2A27` hardware revision read as `"10000"`, causing `protocol_major` to return `None` (probe regex `r"(\d{1,3})(?:\.|$)"` limited digits to 3).
- Status: Solved (hardware session 1 complete with 0 errors/aborts; protocol major parsing open for probe fix before Phase 2).

## 2026-10-13 Review of LIVE-SESSION-1 results
- Problem: results committed the CoreBluetooth UUID and full watch MAC. Fix: masked; history (f4f37cd) open, owner decides.
- Problem: FF10/FF12 reported as OTA; they are unknown writable vendor services. Fix: probe deny list extended, tests. Open: identify statically (smali grep).
- Problem: proposed "fix" of protocol_major would have let the probe send ver=1 where the app sends 0x10 [I]. Fix: parse full integer, compare the truncated byte, refuse; test with "10000". Open: smali check of the cast.

## 2026-10-13 Android HCI snoop capture decode (C900-Q19)
- Evidence: `captures/btsnoop_hci.log.last`, `captures/decoded.txt`, `targets/c900/tasks/results/C900-Q19.md`.
- Findings:
  - Wire version byte settled [H]: App transmits `ver = 0x10` (16) on all 63 frames, matching Claude's inference of `10000 & 0xFF == 0x10`. Watch transmits `ver = 0x01` on its DF frames.
  - Bonding trigger settled [H]: Watch sends unsolicited `cmd 0x0E key 0x01` announcing Classic BT MAC (`XX:XX:XX:XX:XX:XX`), triggering app `createBond()`. Feature bit 15 (`0x40`) confirmed active.
  - Bind handshake settled [H]: App sends `cmd 0x03 key 0` token; watch replies with `cmd 0x0C key 8` (bind accepted) + ACK `x=17 status=1`.
  - Watch ACK formula settled [H]: `FD 00 05 <sum> <cmd> <key> <seq_hi> <seq_lo> <status>` where `status=1` and `x = plen + 9`.
  - Privacy preserved: all personal message text, usernames, and addresses masked/redacted.
- Status: Solved.

## 2026-10-13 Review of C900-Q19 and privacy scrub tooling
- Problem: Q19 kept the watch OUI in three files. Cause: belief that a masked tail is enough. Fix: full mask; new `tools/privacy_scan.py` (flags kept OUIs) and skill `re-privacy-scrub`. History at 91bb5c0 open (owner).
- Problem: Q19 called the time payload a Unix timestamp. Evidence: I-21 decode gives the capture day; codec reproduces bytes. Fix: corrected; I-21 now [C]+[H].
- Problem: ack x called a sequence. Fix: it is the acked frame length; I-18 updated to [H].
- Found by the scan: `re-watch-targets` skill had the Nordic UART UUID as `...B5A9...` (typo, standard is B5A3); fixed. Legacy t900-c900 client and source copy keep the typo (superseded, allow-listed).
- Found by the scan: owner home path in legacy handoff and incident file; masked.

## 2026-10-13 Hardening before handing to the live agent
- Problem: lint did not stop a committed capture or probe log (only .gitignore did). Fix: lint rule + test. Solved.
- Problem: personal-data scan was a separate manual step. Fix: lint runs it over targets/docs/.claude; pre-commit hook installer. Solved.
- Problem: probe hung in a shell without macOS Bluetooth permission (pre-flight incident). Fix: `bt_preflight`, tests. Solved; untested on a real Mac.
- Added `tasks/AGENT-BRIEF.md` (state, never-list, results procedure, decision table).

## 2026-10-13 HCI pairing events check (C900-Q19 second pass)
- Evidence: `captures/btsnoop_hci.log.last`, `targets/c900/tasks/results/C900-Q19.md` Section 7.
- Findings:
  - Wire pairing settled [H]: Time sync ACK (t=2.732s) triggers `HCI_Remote_Name_Request` (t=2.764s) targeting the derived Classic BT address (`ble_mac last byte ^ 0x55`, confirming I-30 path #3).
  - Name resolution timed out [H]: All 3 `HCI_Remote_Name_Request` commands timed out after 12.8s (status 0x04, `Page Timeout`).
  - No Classic connection or keys on the wire [H]: Zero `HCI_Create_Connection`, `Authentication_Complete`, `Simple_Pairing_Complete`, or link key events.
  - Zero LE SMP/encryption [H]: Zero packets on L2CAP CID 0x0006; zero `HCI_LE_Start_Encryption` or `Encryption_Change` events. Transport remained unencrypted.
- Status: Solved.


## 2026-10-13 Codec ver parameter (owner approved)
- Change: `frames.build(cmd, key, payload, ver=DEFAULT_VER)`, `C900_VER = 0x10` [H], `ver_from_hw_revision`, `ack(cmd, key, x, status)`, SimWatch acks with x = frame length; probe derives ver from 0x2A27 and accepts only `REVIEWED_VERS` {0x01, 0x10}. Tests: capture vector (time sync 2026-10-13 16:23:11, ver 0x10), unreviewed ver refuses, "10000" -> 0x10 sent.
- Problem: Q19 excerpts had wrong length bytes (hand-copied). Evidence: ack x and decoder. Fix: noted in Q19 section 8; tests use I-11.

## 2026-10-13 Owner QR observation
- Owner: QR scan in Hiwear Plus connects immediately after unbind. Recorded in results/OWNER-QR-2026-10-13.md. Not a protocol requirement (session 1 connected without it); QR contents [U]; S-22 static check opened. Photos not committed (name, address).

## 2026-10-13 Live Session 2 (safe-write find)
- Evidence: `captures/c900-probe-safe-write-20261013-180232.log`, `captures/c900-probe-safe-write-20261013-180245.log`, `targets/c900/tasks/results/LIVE-SESSION-2-2026-10-13.md`.
- Confirmation fail-safe tested: First run input `j` at confirmation prompt aborted with `SAFETY_STOP confirmation mismatch; nothing sent` (exit code 3). Radio untouched.
- Wire results:
  - Wire version byte confirmed [H]: Probe derived `ver_byte=0x10` from 0x2A27 ("10000"); transmitted frame with `ver=0x10`; accepted by watch.
  - Watch ACK confirmed [H]: `ACK ok cmd=0x02 key=0x0b status=1 x=0x000a x_is_frame_len=True`. Confirms I-18 on direct radio probe without bind.
  - Physical reaction confirmed [H owner]: Watch screen displayed "the bracelet has been found!" with vibration.
  - Invariant I-35 narrowed [H]: Watch executes `find` alert command without requiring a prior bind token (cmd 3 key 0).
- Status: Solved.

## 2026-10-13 S-21 / S-22 static pass
- Problem: jadx/apktool install failed (GitHub release host 403 from the cloud). Fix: androguard from PyPI on the LFS copy (hash checked). Solved for string and method reading.
- Result: FF10/FF12 family not referenced by the app [C negative]; QR = BLE MAC only, `LE` prefix or `?para=` URL, 17 chars [C, BleScanActivity.onActivityResult]. results/S-21-S-22.md.

## 2026-10-13 Phase 3a core
- Built `client/c900-android/core` (Kotlin/JVM) and shared vectors `tests/fixtures/c900_vectors.json` from the Python codec.
- Problem: Google Maven unreachable (no Android Gradle plugin); Maven Central returned 429 for a while. Fix: core is pure Kotlin/JVM; build retried with backoff. App shell open.

## 2026-10-13 Live Session 3 (safe-write message & time)
- Evidence: `captures/c900-probe-safe-write-20261013-183426.log`, `captures/c900-probe-safe-write-20261013-190018.log`, `captures/c900-probe-safe-write-20261013-190223.log`, `targets/c900/tasks/results/LIVE-SESSION-3-2026-10-13.md`.
- Message findings: 24-byte frame transmitted in two pieces (20 B, 4 B). Owner confirmed notification "reWatch test" appeared on watch display [H owner]. Watch emitted `cmd 0x0E key 1` (Classic Bluetooth MAC broadcast), and probe `BOND_TRIGGERS` rule triggered immediate clean disconnect (code 3).
- Time sync findings: 13-byte packed time frame transmitted in single piece. Watch immediately returned `ACK ok cmd=0x02 key=0x01 status=1 x=0x000d x_is_frame_len=True`. Confirms I-18 live (x = 13 == frame length). Zero pairing dialogs triggered on macOS. Exit code 0 across multiple runs.
- Invariant I-35 concluded: Watch executes all three basic safe-write commands (find, message alert, time sync) without requiring an initial bind handshake (cmd 3 key 0).
- Status: Solved.

## 2026-10-13 Robustness pack for parallel agents
- Added `tasks/robust/` (README framework, template, R01-R04, R06-R10, PROMPT) and `tools/dexgrep.py` + `requirements-static.txt` (androguard reader for machines without jadx).
- R05 dropped from the pack; not written.
- Notes from reviewing LIVE-SESSION-3: message ack never received (probe stopped on unsolicited 0x0E/1); several `time` runs although the sheet said no retries; "zero link keys created" cannot be known on macOS. Handed to R09 to word corrections.

## 2026-10-13 Robustness pack integration (Claude, integrator)
- Merged `c900/r01`..`c900/r10` (each touched only its own lane; no conflicts) onto the work branch.
- Spot checks with `tools/dexgrep.py`: confirmed 196-byte cut, queue cap 5, `isNewMsgPushSetting`, write retry sleeps 20/100 ms, reconnect delays 3000/10000/2000, cmd 5 key 7/8 log strings.
- Rejected, R05 units: cites `FormatUtils->getDistance/getCalories` and `DevBaseDataUtils->getHrDataList/getDeviceTempBeanList` and a `SPORT_DATA_TIME_OUT` constant; none exist in the pinned APK. Units stay [U]. Also rejected R05's frame hex column: it uses an `ab ...` header that is not this protocol (frames start DF/FD, PROTOCOL §4).
- Rejected, R03 retry summary ("3 attempts then disconnect" for every write): coarser than and partly wrong against PROTOCOL §3 (frames of 20 bytes or less get no retry; remainder piece one retry after 20 ms).
- Not applied, R01 proposal to stop prompting on inbound 0x0E key 1: the watch sends it after a message push (LIVE-SESSION-3), so the prompt will be frequent, but silently dropping it is a design decision for the owner. Open.
- Not applied, R02 proposed limits (500 ms between messages, 3 s find cooldown): no evidence for the values; the core keeps one-in-flight plus the 200-write budget.
- Coordinator handoff summary did not match the result files (it listed a 1 s debounce, 100 ms dial pacing, 27 inbound commands 0x01..0x22, "pure reactive peripheral"); the result files were used, not the summary.
- Core fixes from R08 applied with tests: F-01 reads in any order, F-02 foreign ack dropped instead of failing the in-flight command, F-03 short UUIDs, F-04 inbound capped at 256, F-05 pacing contract documented on `CommandQueue`; R07's note: `Frames.Inbound.Cmd` equality is structural.
- Kotlin changes were not compiled or run in the cloud session: Maven Central returned 429 three times. Run `gradle :core:test` on the owner machine before merging.

## 2026-10-13 Follow-up static pass (Claude, cloud)
- Units settled [C]: `HomeFragment.lambda$updateStepDataAndProgress$15` divides day-total distance and calorie by 1000.0f (float bits 0x447A0000) and multiplies km by 0.621 for miles; `StepUtils.getTotalStepData` stores raw u32 values; `HexUtil.byte2IntLR` is big-endian. So meters and calories. R05's citations for the same answer were invalid (classes not in the APK).
- R04 corrected: `getNewType` gives 13 for "other" (R04 said 255) and -1 for unmapped or switched-off apps, which `onAppMsgReceive` does not push. C900-Q04 §5 already had the right table.
- Core: added `HealthSync` (inbound-only cmd 5 marker tracker plus key 12 decoder), built ahead of a full-sync capture; idle timeout 30 s is a placeholder [I]. Tests added; not run here (Maven 429), see LIVE-NEXT task 1.
- privacy_scan: strict mode reported DF/FD frame headers as MACs. Now skips a 6-byte run that starts inside the 9-byte frame header (it cannot hold a whole MAC); runs starting in the payload are still flagged. Three third-party example payloads in `sources/legacy-t900-c900-PROTOCOL.md` allowlisted by exact value. `targets/c900` strict scan: 0 findings.
- PROTOCOL §10 unknowns updated with the settled rows.

## 2026-10-14 G4 local verification: Kotlin core tests and distance/calorie units
- Evidence: `client/c900-android/core/build/test-results/test/TEST-*.xml`, `captures/btsnoop_hci.log.last`, `work/c900-apk/com.myled.HiwearPlus.apk` (classes2.dex smali).
- Task 1: Kotlin core tests compiled and executed locally with JDK 21 and Gradle 8.10.2 (`gradle :core:test`). 26 tests passed across `CoreTest` (17 tests), `FuzzTest` (7 tests), and `HealthSyncTest` (2 tests), 0 failures, 0 skipped.
- Task 2: Distance and calorie units settled [C] in APK bytecode across both Key 12 and Key 2. In `captures/btsnoop_hci.log.last`, all cmd 5 key 12 total steps frames carried all zeros (`000000000000000000000000`) and 0 key 2 frames were present due to pre-capture device unbind. APK bytecode inspection of actual UI consumer classes revealed:
  - `HistoryStepAdapter.getView` (classes2.dex lines 235-297): calls `DayMinuteStepEntity.getDistance()` and divides by `1000.0f` (`const/high16 1148846080`). Formats with `0.00` + string resource `0x7f13054c` (`Km`), or multiplies by `0.621371` for imperial `0x7f130392` (`Miles`). Calls `DayMinuteStepEntity.getCalorie()` and divides by `1000.0f`, formatting with `%.2f` + string resource `0x7f130550` (`Kcal`).
  - `HomeFragment.lambda$updateStepDataAndProgress$15`: parses `DayStepEntity.getDistance()` and `DayStepEntity.getCalorie()`, dividing both by `1000.0f` before display.
  - Conclusion: Wire distance integer is meters (m), wire calorie integer is calories (cal). Both scale by 1/1000. Tag: [C].
- Owner decision on `cmd 0x0E key 1` bond prompts: Owner selected option (c) ("i want this to be automatic run while i sleep kind of thing"): never prompt the user; cache the Classic BT MAC address silently and send protocol ACK, allowing unattended background operation while the owner sleeps without popups. Recorded in `targets/c900/CLIENT-DESIGN.md`.

## 2026-10-14 Review of 8c7918a (Claude, cloud)
- Accepted: steps.md append-only; `HistoryStepAdapter.getView` citation rechecked with dexgrep (`getDistance`/`getCalorie` on `DayMinuteStepEntity`, `div-float` by 1000.0f).
- Problem: CLIENT-DESIGN recorded the owner's "never prompt on 0x0E key 1" decision, but `Session.onCommand` still returned `AskUserBond` for it. Fixed: 0x0E key 1 now caches `classicMac` (memory only) and acks; 0x0C key 19 still prompts. Test updated in `CoreTest.sessionFlowLikeRealWatch`. Not compiled in the cloud (Maven 429); rerun `gradle :core:test` on the owner machine.

## 2026-10-14 G4 Android app shell implementation (Antigravity, local)
- Added `:app` module in `client/c900-android` depending on `:core`, building debug APK (`gradle :app:assembleDebug`).
- Built components:
  - `MainActivity`: plain Activity without Compose.
  - `PacingScheduler`: strict single-GATT-operation-in-flight queue with 20 ms piece pacing and denied-UUID drop.
  - `GattLink`: Android `BluetoothGatt` adapter mapping `Session.Action` to GATT calls, feeding frames to `FrameReader`.
  - `WatchService`: `connectedDevice` foreground service owning `Session`, `CommandQueue`, `HealthSync`, with 10000 ms disconnect / 3000 ms connect failure reconnect delays, silent cache for 0x0E key 1, and prompt notification for 0x0C key 19 (never calls `createBond`).
  - `NotificationMapper`: package-to-type mapper implementing C900-Q04 section 5 new table (23 apps, Other=13, -1 ignored).
  - `DisconnectedMessageQueue`: bounded FIFO holding newest 5 messages during disconnect.
  - `NotifyListener`: `NotificationListenerService` forwarding notifications via `Commands.message`.
  - Manifest permissions strictly as R10: `BLUETOOTH_SCAN (neverForLocation)`, `BLUETOOTH_CONNECT`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_CONNECTED_DEVICE`, `POST_NOTIFICATIONS`, `BIND_NOTIFICATION_LISTENER_SERVICE`. Zero `INTERNET` permission.
  - Privacy: zero logging of notification text, MAC addresses, or device names.
- Tests passing:
  - Gradle: 26 `:core` tests + 9 `:app` tests = 35 JVM unit tests pass (0 failures).
  - Python: 150 tests pass (`unittest discover -s tests`).
  - Linter: `python3 tools/rw.py lint` (0 problems).
  - Privacy scan: `python3 tools/privacy_scan.py targets/c900 docs --strict` (0 findings).
- What is untested on a device (static/JVM only):
  - Actual Android BLE stack GATT connection, MTU negotiation, and service discovery on a physical watch.
  - Real timing of Android `onCharacteristicWrite` callbacks with Bluetooth hardware controller.
  - Real OS behaviour of `NotificationListenerService` permission grant flow by user.
  - Live reconnection backoff in sleep/doze mode on physical Android device.
  - Actual watch display rendering of pushed notifications via `:app` shell.
