# C900 watch

- Slug: c900
- Created: 2026-10-12, re-planned 2026-10-13
- Goal: map the Hiwear Plus protocol for an open-source ad-free C900 client; **plan and evidence first**, implementation deferred (see PLAN.md). Long-term: pair, time sync, notifications, battery; watch faces only after a reviewed design (OTA path).

## Assumptions (defaults chosen without asking)
- Companion app is Hiwear Plus `com.myled.HiwearPlus` [owner statement 2026-10-13; package from the Play listing, W]. The earlier HryFine/HiWatch Pro assumption is superseded (FACTS.md section 1).
- Static analysis only; the app is never installed or run; no vendor server calls.
- Reads only on the watch until the owner approves a write session. Never touch 0xFF00, 0x18A8, `6E40FF01...` or commands 0x01, 0x06, 0x07, 0x0D, 0x13.
- Client in `client/c900/` is **deferred** (PLAN.md Phase 3). Codec sketch exists: frame layout and CommandID opcodes [C], blocklist on dangerous ids; UNVERIFIED on hardware. No new client features until Phase 3 approval.

## Invariants
Read [INVARIANTS.md](INVARIANTS.md) before editing any c900 doc or code; `tests/test_c900_invariants.py` guards the checkable rows.

## Gate status
| Gate | Status | Notes |
|---|---|---|
| G0 Brief | done | re-planned for Hiwear Plus |
| G1 Acquire | done | 2.0.1 / 31 pinned (SOURCES.md); owner-approved repo copy at `resources/c900/hiwear-plus-2.0.1.xapk.zip` (Git LFS) |
| G2 Surface map | done | PROTOCOL.md sections 1 to 3, 8 |
| G3 Spec | done | framing, command tables, inbound map, bond conditions, cmd 5 field maps [C], capture settled [H] |
| G4 Client | done (built, not run on hardware) | pure Kotlin `:core` (codecs, Session, CommandQueue, HealthSync with cmd 5 decoders) + `:app` shell (GattLink, PacingScheduler, WatchService, plain SQLite local storage, settings & status screens); verified against SimWatch and unit tests (81 Kotlin tests pass) |
| G5 Handoff | ready for live run | LIVE-APP-1 run sheet authored (budget <= 3 writes); awaits owner-attended session (Part B) |

## Owner capture (optional)
To record the vendor app's Bluetooth traffic on your own Android phone, follow `docs/guides/HCI-CAPTURE-ANDROID.md`. First-contact plan: `tasks/HW-0-RUNSHEET.md` (DRAFT).
