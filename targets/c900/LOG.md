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
