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
