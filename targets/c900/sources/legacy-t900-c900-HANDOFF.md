<!-- Imported 2026-10-13 from the removed combined target targets/t900-c900/HANDOFF.md. Kept for history. C900 parts are SUPERSEDED: they assumed HryFine/HiWatch Pro and were written from a third-party write-up, not from the app. Current C900 facts: ../PROTOCOL.md and ../FACTS.md. -->

# Handoff: T900 and C900 watch

## What exists
- Target documentation:
  - [TARGET.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/TARGET.md): Goals, assumptions, and hardware/software ecosystem mapping.
  - [SOURCES.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/SOURCES.md): Package identities (`com.lianhezhuli.hyfit` for HryFine, `com.jusheng.hiwatchpro` for HiWatch Pro), mirror provenance, and clean-room source references.
  - [FACTS.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/FACTS.md): Single source of truth for disputed vendor specs, panel resolutions, and SoC architectures.
  - [PROTOCOL.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/PROTOCOL.md): Byte-exact wire specifications for HryFine NUS (`0xDF`/`0xFD` Sum8) and JieLi RCSP (`0xFE 0xDC 0xBA` ... `0xEF`), dial format, and worked vectors.
  - [LOG.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/LOG.md): Problem and decision ledger across all gates.
- Layered Client (`client/t900-c900/`):
  - `t900_c900.codecs`: Pure frame packers and parsers for HryFine NUS and JieLi RCSP.
  - `t900_c900.dial`: RGB565 watch face binary compiler and parser.
  - `t900_c900.safe_write`: Flash wear mitigation guard with delta skip, daily cap, and interval enforcement.
  - `t900_c900.link`: Abstract link protocol, `RecordingLink` for simulation, and `BleakLink` for real Bluetooth.
  - `t900_c900.session`: Async session state machine for probe, status, time sync, notifications, and dial push.
  - `t900_c900.simulator`: Standalone device simulator implementing C900 and T900 protocol responders.
  - `t900_c900.cli`: Command-line interface with `--dry-run` and `--simulate` options.
- Test Suite:
  - 30 unit and integration tests passing (`PYTHONPATH=client/t900-c900 pytest -q client/t900-c900/tests` or `unittest`).
  - `test_no_vendor_calls.py` ensures 100% offline local-only operation without analytics or vendor cloud servers.

## Evidence summary
Statement tags in [PROTOCOL.md](file:///Users/<owner>/Desktop/reWatch/targets/t900-c900/PROTOCOL.md):
- `[C]` (Confirmed in artifact / clean-room SDK baseline): 12
- `[V]` (Verified by test vectors / emulation / script): 7
- `[H]` (Confirmed on real hardware): 1
- `[W]` (Third-party report / documented community teardown): 46
- `[I]` (Inferred from architecture standards): 6
- `[U]` (Unknown / varies across hardware batches): 1

## What only hardware can settle
| Unknown | Test | Pass / fail criterion |
|---|---|---|
| C900 NUS UUID variant (`0x9F` vs standard `0x9E`) | Run read-only probe: `t900-c900 --address <MAC> probe` | Success if NUS service discovered; identifies whether batch ends in 0x9F or 0x9E |
| T900 Authentication Requirement | Connect in read-only mode and monitor 0xAE02 notifications | If 0x00 challenge received, device enforces E1/SAFER+ handshake; if not, accepts open RCSP |
| Real LCD Panel Resolution | Run dial push with 240x286 vs 320x385 dial package | Watch displays image cleanly without tearing, wrapping, or aspect-ratio distortion |
| Maximum ATT Chunk Size | Measure packet roundtrip with 20B, 128B, and 240B MTU | Identifies maximum MTU accepted without buffer overflow |
| Cosmetic Sensor Reality | Place watch on non-living object (table, mug) | Confirms synthetic pulse generator (72-85 bpm) vs real photodiode response |

## First hardware session checklist
1. **Pre-flight**:
   - Verify battery is charged above 50%.
   - Ensure the official vendor app is uninstalled or Bluetooth permission is revoked on nearby phones.
2. **Read-only probe first**:
   - Run `python -m t900_c900.cli --address <MAC> probe --qualify`
   - Confirm discovered services. Verify that hazardous OTA bootloader (`0x18A8`, Cus5610, `0xAE10`) is NOT accessed.
3. **Capture reference traffic**:
   - If owner approves, capture an Android HCI snoop log during pairing and time sync using the vendor app for 60 seconds.
   - Run `python tools/btcap.py <snoop.log>` to confirm packet framing.
4. **Budgeted writes only**:
   - Execute one safe write at a time: `t900-c900 --address <MAC> time-sync`.
   - Observe watch display clock update.
   - Test alert notification: `t900-c900 --address <MAC> notify --title "reWatch" --message "Test"`.
   - Dial upload: test with a solid color test dial using safe-write protection.

## Risks and Bricking Hazards
- **OTA Bootloader Deathtrap (CRITICAL HAZARD)**: Never issue write commands to Service `0x18A8` (Cus5610) or JieLi OTA `0xAE10`. Bluetrum and JieLi budget bootloaders lack write-protection boundaries and will overwrite running code mid-transfer, bricking the device permanently. The client hard-blacklists these services.
- **Flash Memory Wear**: Budget watches use low-grade SPI NOR flash (2 MB to 8 MB) with limited erase cycle endurance. The safe-write guard enforces a maximum daily write cap (50 writes) and delta skipping to prevent wear.
