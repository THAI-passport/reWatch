# Problem log: T900 and C900 watch

Append every pitfall, newest last. Entry: date, gate, problem, cause, solution (or Status: Unsolved plus what was tried).

---
- 2026-10-12 | G0 | Doctor missing tools | jadx, apktool, and adb not present in system PATH | Python stdlib and test harness functional; apktool/jadx available via setup_tools.py if binary decompilation is needed |
- 2026-10-12 | G0 | Model divergence | T900 and C900 use distinct SoCs (JieLi Pi32 vs Bluetrum RISC-V) and different apps (HiWatch Pro vs HryFine) | Support modular profiles in client/t900-c900/ rather than assuming a single monolithic protocol |
- 2026-10-12 | G1 | Mirror bot challenge | curl to d.apkpure.com returned HTTP 403 Cloudflare challenge | Halted automated scraping per ground rules; verified official package identities (com.lianhezhuli.hyfit and com.jusheng.hiwatchpro) and derived wire protocol clean-room from ultra_budget_smartwatch_reconnaissance.md |
- 2026-10-12 | G2 | OTA bootloader risk identified | Bluetrum Cus5610 (0x18A8) and JieLi OTA services lack memory boundary checks and brick devices upon write | Hard-blacklist OTA service UUIDs in client transport layer; permit only runtime GATT/NUS/RCSP characteristics |
