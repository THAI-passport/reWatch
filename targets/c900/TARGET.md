# C900 watch

- Slug: c900
- Created: 2026-10-12, re-planned 2026-10-13
- Goal: pair, time sync, notifications, read battery from a Python CLI; watch faces only after a reviewed design (they ride on the OTA path)

## Assumptions (defaults chosen without asking)
- Companion app is Hiwear Plus `com.myled.HiwearPlus` [owner statement 2026-10-13; package from the Play listing, W]. The earlier HryFine/HiWatch Pro assumption is superseded (FACTS.md section 1).
- Static analysis only; the app is never installed or run; no vendor server calls.
- Reads only on the watch until the owner approves a write session. Never touch 0xFF00, 0x18A8, `6E40FF01...` or commands 0x01, 0x06, 0x07, 0x0D, 0x13.
- Client in `client/c900/`. Its codec was built ahead from a third-party layout; the frame layout now matches the app [C], the opcodes in it do not (FACTS.md section 3).

## Gate status
| Gate | Status | Notes |
|---|---|---|
| G0 Brief | done | re-planned for Hiwear Plus |
| G1 Acquire | done | 2.0.1 / 31 pinned (SOURCES.md); owner-approved repo copy at `resources/c900/hiwear-plus-2.0.1.xapk.zip` (Git LFS) |
| G2 Surface map | done | PROTOCOL.md sections 1 to 3, 8 |
| G3 Spec | doing | framing, command table, time packing, OTA D5/D6 framing [C]; PAR container bytes still [U] (native) |
| G4 Client | doing | opcodes match CommandID; blocklist enforced; UNVERIFIED on hardware |
| G5 Handoff | todo | after HW-2 |
