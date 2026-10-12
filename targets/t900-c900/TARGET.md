# T900 and C900 watch

- Slug: t900-c900
- Created: 2026-10-12
- Goal: scan, connect, read basic status and push a watch face or notification from a Python CLI

## Assumptions (defaults chosen without asking)
- Static analysis and clean-room protocol engineering only; the target app is never installed or run.
- Android companion app first; Python client; local-only, no vendor server calls.
- Hardware first, hardware last: no hardware contact or firmware modification without explicit written approval.
- T900 and C900 are distinct ODM product streams: T900 is predominantly JieLi architecture (JL7012/AC6954/AC6958) paired with HiWatch Pro (`com.jusheng.hiwatchpro`), while C900 is predominantly Bluetrum architecture (AB53xx/AB56xx) or JieLi variants paired with HryFine (`com.lianhezhuli.hyfit` / `com.yscoco.watch`). The client must support modular profiles rather than assuming a single monolithic protocol.
- Evidence tags: [C] confirmed in artifact, [V] verified by emulation or vector, [H] hardware, [W] third-party, [I] inferred, [U] unknown.

## Gate status
| Gate | Status | Notes |
|---|---|---|
| G0 Brief | done | Slug, goal, assumptions, and hardware/software scope defined |
| G1 Acquire | done | Identified packages com.lianhezhuli.hyfit and com.jusheng.hiwatchpro; clean-room wire spec |
| G2 Surface map | done | Mapped NUS (C900), JieLi RCSP (T900), standard GATT, and prohibited OTA UUIDs |
| G3 Spec | done | Byte-exact PROTOCOL.md with HryFine 0xDF/0xFD framing, JieLi RCSP, dial format, worked vectors |
| G4 Client | todo | |
| G5 Handoff | todo | |

## Hardware and software identified
| Item | Value | Tag | Source |
|---|---|---|---|
| T900 SoC | JieLi JL7012 / AC6954 / AC6958 (32-bit Pi32 core, dual-mode BT 5.3) | [W] | ultra_budget_smartwatch_reconnaissance.md |
| T900 Companion App | HiWatch Pro (`com.jusheng.hiwatchpro`) | [W] | ultra_budget_smartwatch_reconnaissance.md; Google Play store listing |
| T900 Transport | JieLi RCSP over service 0xAE00 (char 0xAE01 write, 0xAE02 notify) | [W] | ultra_budget_smartwatch_reconnaissance.md; re-jieli skill |
| C900 SoC | Bluetrum AB53xx / AB56xx (32-bit RISC-V core) or JieLi variants | [W] | ultra_budget_smartwatch_reconnaissance.md |
| C900 Companion App | HryFine (`com.lianhezhuli.hyfit` / `com.yscoco.watch`) | [W] | ultra_budget_smartwatch_reconnaissance.md; Google Play store listing |
| C900 Transport | Nordic UART Service (NUS) emulation (`6E400001-B5A3-F393-E0A9-E50E24DCCA9F`) | [W] | ultra_budget_smartwatch_reconnaissance.md |
| Standard GATT | Battery Service (`0x180F` / `0x2A19`), Device Info (`0x180A`) | [W] | ultra_budget_smartwatch_reconnaissance.md; re-watch-targets |
| Biometric Sensors | Cosmetic only (0805 green LEDs + firmware timer producing 72-85 bpm) | [W] | ultra_budget_smartwatch_reconnaissance.md §4.1 |

## Open questions
- Whether specific C900 hardware revisions advertise standard Nordic UUID (`...DCCA9E`) or vendor variant (`...DCCA9F`) [U]. Client must probe and accept both.
- Whether T900 JieLi firmware requires E1/SAFER+ authentication handshake before accepting RCSP commands [U].
- Watch face dial dimensions across model variants: 240x286 vs 320x385 pixels [U]. Client profile system must handle both.
