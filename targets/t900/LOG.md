# Problem log: T900 watch

Append every pitfall, newest last. Entry: date, gate, problem, cause, solution (or Status: Unsolved plus what was tried).

---

## 2026-10-12 G1 blocked: artifact not reachable
- Evidence: APK mirror and release hosts are blocked from the cloud sandbox (recorded in the next-pass prompt, same date); no lookup made this pass.
- Cause: environment network policy.
- Fix: open. Needs the owner to supply the XAPK for `--local-file`, or the host added to the allowed domains.
