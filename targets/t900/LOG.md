# Problem log: T900 watch

Append every pitfall, newest last. Entry: date, gate, problem, cause, solution (or Status: Unsolved plus what was tried).

---

## 2026-10-12 G1 blocked: artifact not reachable
- Evidence: APK mirror and release hosts are blocked from the cloud sandbox (recorded in the next-pass prompt, same date); no lookup made this pass.
- Cause: environment network policy.
- Fix: open. Needs the owner to supply the XAPK for `--local-file`, or the host added to the allowed domains.

## 2026-10-13 G0 duplicate target layout removed
- Evidence: three target folders existed after the 2026-10-12 merges: `t900`, `c900` and a combined `t900-c900` with its own task pack and a separate client in `client/t900-c900/`.
- Cause: two branches created targets for the same watches in parallel.
- Fix: one folder per watch. The combined folder was removed; its text is kept once under `targets/c900/sources/legacy-t900-c900-*.md`; T900 parts folded into PROTOCOL.md section 9 as [W]. The client in `client/t900-c900/` is kept, marked built-ahead and unverified.
