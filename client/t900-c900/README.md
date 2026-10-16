> Status 2026-10-13: BUILT AHEAD and UNVERIFIED. Written from a third-party write-up before any artifact was read. The C900 now pairs with Hiwear Plus (`com.myled.HiwearPlus`), not HryFine; see `targets/c900/PROTOCOL.md` for what the app actually does. Do not use against a real watch.

# T900 and C900 Smartwatch Client

Open-source, clean-room local-only Python client and simulator for C900 Ultra (Bluetrum/HryFine ecosystem) and T900 Ultra (JieLi/HiWatchPro ecosystem) smartwatches.

Features:
- Pure offline operation with zero vendor network or analytics calls.
- Dynamic transport negotiation: HryFine NUS variant (`...DCCA9F`), standard Nordic NUS, or JieLi RCSP (`0xAE00`).
- Strict OTA blacklist protecting devices from bricking risks on service `0x18A8` (Cus5610) and `0xAE10`.
- Safe-write guard with delta skipping, rate limiting, and daily caps to prevent NOR flash wear.
- Built-in software device simulator for test and verification without hardware.
- Full CLI supporting read-only probing, status queries, time synchronization, notification push, and watch face compilation.
