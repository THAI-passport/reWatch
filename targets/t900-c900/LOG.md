# Problem log: T900 and C900 watch

Append every pitfall, newest last. Entry: date, gate, problem, cause, solution (or Status: Unsolved plus what was tried).

---
- 2026-10-12 | G0 | Doctor missing tools | jadx, apktool, and adb not present in system PATH | Python stdlib and test harness functional; apktool/jadx available via setup_tools.py if binary decompilation is needed |
- 2026-10-12 | G0 | Model divergence | T900 and C900 use distinct SoCs (JieLi Pi32 vs Bluetrum RISC-V) and different apps (HiWatch Pro vs HryFine) | Support modular profiles in client/t900-c900/ rather than assuming a single monolithic protocol |
