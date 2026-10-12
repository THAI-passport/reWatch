# C900 watch

- Slug: c900
- Created: 2026-10-12
- Goal: pair, time sync, watch-face upload, notifications from a Python CLI

## Assumptions (defaults chosen without asking)
- Static analysis only; the target app is never installed or run.
- Android companion app first; Python client; local-only, no vendor server calls.
- Scope: pairing, time sync, watch-face upload, notifications. Health telemetry skipped (landscape doc says it is cosmetic [W]).
- Companion app assumed to be HryFine (`com.yscoco.watch`) [W], from `docs/recon/budget-smartwatch-landscape.md`; not yet confirmed by a lookup or the artifact. Whether T900 and C900 share an app or protocol is a finding to make, not an assumption.
- Reads only. OTA and bootloader services (0x18A8, Cus5610, Jieli OTA) are never touched; watch-face writes need the write budget and owner approval.
- Client lives in `client/c900/` in this repo, not in reBeamBox (overrides section 7.3 of the landscape doc).
- Evidence tags: [C] confirmed in artifact, [V] verified by emulation or vector, [H] hardware, [W] third-party, [I] inferred, [U] unknown.

## Gate status
| Gate | Status | Notes |
|---|---|---|
| G0 Brief | done | |
| G1 Acquire | blocked: needs human | APK hosts blocked from the sandbox (2026-10-12); owner to supply the XAPK, then `python tools/rebuild_analysis.py c900 --local-file <path>` |
| G2 Surface map | todo | |
| G3 Spec | todo | |
| G4 Client | doing | frame codec and simulator built ahead from [W] layouts (`client/c900/frames.py`, `tests/test_c900_frames.py`); no transport yet |
| G5 Handoff | todo | |

## Hardware and software identified
| Item | Value | Tag | Source |
|---|---|---|---|
| Companion app | HryFine `com.yscoco.watch` | [W] | landscape doc 3 |
| SoC | variable: Jieli or Bluetrum (AB53xx/AB56xx) | [W] | landscape doc 2, 4 |

## Open questions
