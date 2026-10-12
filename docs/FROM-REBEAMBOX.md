# Carried over from reBeamBox

Worked example and source of the lessons: https://github.com/THAI-passport/reBeamBox (a round BLE e-badge: three transports, Jieli RCSP with E1/SAFER+ auth, Wi-Fi camera mode). reWatch was seeded from reWork (https://github.com/THAI-passport/reWork), which was distilled from it.

## Carried over (generalised, no badge values except as labelled examples)
- Gates G0 to G5, evidence tags `[C] [V] [H] [W] [I] [U]`, FACTS.md as the single place for disputed values.
- Problem log per target, tooling log, FIXES.md.
- Rebuildable artifacts: SOURCES with machine-readable fields, `tools/rebuild_analysis.py`, hash pinning, "rebuild only when necessary", "record after every pass".
- Static analysis skills (`re-static`, `re-acquire`, `re-protocol-spec`, `re-native-emulation`, `re-client-sim`, `re-hardware-recon`) and the recon task pack.
- Safe-write ideas (counter, delta skipping, minimum interval, daily cap) as a rule, in `re-client-sim`.
- Tools: `rw.py`, `btcap.py`, `crcfind.py`, `notify_log.py`, `make_test_media.py`, `setup_tools.py`, `rebuild_analysis.py`, `recover-failed-methods.sh`.
- New in reWatch, generalised from reBeamBox docs: skills `re-jieli`, `re-ble-android-patterns`, `re-capture-ingestion`, plus the watch-specific `re-watch-targets`, and `docs/SOP.md`.

## Left behind on purpose
- Every badge value outside examples: UUIDs (01F0, C2E6FD00 and others), frame layouts of the nn20 and control channels, media containers, picture sizes, name filters, model profiles.
- The `rebeambox` client package, its software badges and tests, `tools/replay_pcap.py` and the synthetic fixtures (they decode that badge's frames; the generic reader is `tools/btcap.py`).
- The Web Bluetooth harness `ui/`, streaming prototype and benchmarks.
- Decompiled code, APKs, native libraries (never committed anywhere).
- The badge's docs: PROTOCOL.md, FACTS.md, models, Wi-Fi protocol, hardware checklists. Read them in the reBeamBox repo when you need a worked example of a finished spec.

## Where to look in reBeamBox for a worked example
| Topic | File in reBeamBox |
|---|---|
| Byte-exact spec with Confirmed/Inferred labels | docs/PROTOCOL.md |
| Fact sheet for disputed values | docs/FACTS.md |
| Procedure and tooling rationale | docs/SOP.md |
| Pitfall log | docs/problem_solution.md |
| Jieli RCSP and auth | docs/PROTOCOL.md sections 3.7 and 3.7.1, `rebeambox/jl_auth.py`, `tools/emulate_jl_auth.py` |
| Wi-Fi path | docs/wifi-protocol.md |
| Hardware test plan | docs/hardware-test-v1.md |
