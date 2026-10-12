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
