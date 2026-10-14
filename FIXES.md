# Fixes

Things that need fixing in reWatch itself (tools, templates, skills), and things already fixed. Add to Open when you find something; move to Fixed with what was wrong and what changed. Same commit as the change.

## Open
- Skills and tools are untested end to end on a real target; run the benchmark in README.md and record gaps here.
- `tools/setup_tools.py` pins jadx and apktool versions and verifies SHA-256 only when `JADX_SHA256`/`APKTOOL_SHA256` are set (it prints the computed hashes); the JDK is the latest 17. Pin real hashes once a machine with github access has downloaded them.
- Windows is untested locally: CI covers `rebuild_analysis.py` and `setup_tools.py`, but the fake-jadx tests skip there and a real run on Windows has not happened. macOS is likewise untested locally (the JDK bundle layout is unit tested).
- The ipa and firmware kinds of `rebuild_analysis.py` verify the hash only.
- Cloud sessions: apkpure, adoptium and github release hosts are blocked unless the environment allows them (README, AGENTS.md).
- iOS, desktop and firmware notes in the skills are thin.

## Fixed
- Cloud builds of the C900 Android app (2026-10-14): `dl.google.com` was blocked and Maven Central (`repo.maven.apache.org`) returned 429. Fix: the owner allowed `dl.google.com` and `maven.google.com` in the environment; the SDK comes from `sdkmanager` (platforms;android-35, build-tools;35.0.0) into `~/tools/android-sdk`; a machine-local `~/.gradle/init.d/central-mirror.gradle` rewrites Maven Central to `https://maven-central.storage-download.googleapis.com/maven2/` (the Gradle plugin portal does not help: it redirects to Central). Nothing in the repo build changes. Verified: `:core:test` 26, `:app:testDebugUnitTest` 23, `:app:assembleDebug` OK on Linux.
- C900 Kotlin core (2026-10-13, R08): session setup failed when info reads finished out of order; a foreign ack failed the in-flight command; short UUIDs crashed `readResult`; `Session.inbound` grew without bound; `Frames.Inbound.Cmd` compared payload by identity. Fixed in `Session.kt`, `CommandQueue.kt`, `Frames.kt` with tests.
- Before-handoff hardening (2026-10-13): `rw.py lint` now rejects tracked capture files and probe logs (btsnoop, pklg, pcap, bugreport zips, `captures/`, `c900-probe-*.log`; synthetic test fixtures exempt) and runs the personal-data scan over `targets/`, `docs/`, `.claude/`; `tools/install_hooks.py` adds an opt-in pre-commit hook; `tools/c900_probe.py` fails fast (`bt_preflight`) when macOS Bluetooth permission is denied/restricted, or not determined in a non-interactive shell, instead of hanging; `targets/c900/tasks/AGENT-BRIEF.md` is the one-page brief for live agents. Tests added.
- No mechanical check for personal data in result files (three leaks on 2026-10-13: Mac address, CB UUID and watch MAC, watch OUI): added `tools/privacy_scan.py`, `.privacy-allow`, tests, skill `re-privacy-scrub`; fixed the Nordic UART UUID typo in `re-watch-targets`.
- `tools/notify_log.py` subscribed to every notifiable characteristic, OTA/DFU included: added a default deny list (0xFF00, 0x18A8 and their characteristics, `...dcca9e`), `--deny`, `--only` (denied UUID there exits 2 before anything is enabled), and a printed plan before listening; tests in `tests/test_notify_log.py` (C900-Q17).
- Pinning was only a hash check: added the pin rule to AGENTS.md, `COPY_LOCATION` and URL2 guidance in the SOURCES template, pin warnings and clearer mismatch and accept messages in the rebuild tool, with tests.
- Hash mismatch after a vendor update now names the real version; URL2 to URL4 fallbacks; rebuild-only-when-necessary and record-after-every-pass rules in AGENTS.md and the skills; QUICKSTART in the task-pack template; test that scripts mentioned in docs exist.
- Hardware recon had no reusable form that a weaker agent could follow: added `templates/tasks/` (README, SW-RECON, HW-RECON, ASSUMPTIONS, STATUS) copied by `rw.py init`, the `re-hardware-recon` skill, `tools/notify_log.py`, `tools/make_test_media.py`, and rules in `re-client-sim` (log pushed status, no-delta option) and `AGENTS.md` (writing for weaker agents). Derived from the reBeamBox task pack.
- Rebuild and setup were bash-only (`sha256sum`, `declare -A`, linux-x64 JDK URL), so they failed on macOS and Windows: rewrote both in Python 3 standard library (`rebuild_analysis.py`, `setup_tools.py`), kept the .sh files as wrappers, added OS/arch detection, the macOS JDK bundle layout, zsh PATH line, apktool.bat, and tests.
- jadx was OOM-killed on small machines and the cap lived only in the log: `rebuild_analysis.py` takes `--max-heap`/`JADX_HEAP` and defaults to 3g under 8 GiB RAM; an OOM kill now says so.
- `?version=latest` URLs break the hash check on a new release: `--url` overrides the download URL.
- No script rebuilt a target's artifacts and decompiled tree on another machine: added `tools/rebuild-analysis.sh` (SOURCES driven, hash-verified, idempotent), a machine-readable block in `templates/SOURCES.md`, and pinned jadx and apktool in setup-tools.

### 2026-10-13 — pinned vendor archive for cloud rebuild
- Wrong: no way to rebuild a target whose download host is blocked or unsigned without the user uploading the file each time; committing binaries was flatly forbidden.
- Changed: owner-approved exception under `resources/<slug>/` via Git LFS + `REPO_COPY` / `REPO_COPY_SHA256` in SOURCES; lint enforces declaration; rebuild extracts the single inner member after hash check.

### 2026-10-13 - c900 probe DEEP-PASS-1
- Wrong: pairing detection relied on `BleakClient.is_paired`, which bleak 3.0.2 does not have (always False); writes/subscribe used UUID strings across the whole GATT table; the version byte was sent as 1 without checking 0x2A27; the scan log stored third-party names and full manufacturer data; 0x2A25 logged in clear; stale acks accepted; no inbound flood cap; `--log-dir` could point into tracked paths; C1/bidi characters passed sanitize; the test fake never exercised Device Information reads.
- Changed: `pair_state`, `command_chars`, `protocol_major` refuse, scan/inspect redaction, `add_secret`, armed ack, `FrameReader` caps, `check_log_dir` and exclusive log create, bounded CLI times, 20 ms piece gap; 17 tests in `DeepPass1Fixes` (targets/c900/tasks/results/DEEP-PASS-1.md).

### 2026-10-13 — c900 probe hardening
- Wrong: `_require_command_layout` had an impossible `and` check on OTA lookalike write chars and didn't verify parent service; `is_ota_uuid` missed custom 5610 UUIDs; `mode_safe_write` missed pairing check during wait; `on_notify` locked up on leading non-header byte; `redact_line` failed without exact keyword "payload"; write cap pre-check had a `pass` statement allowing partial frame sends.
- Changed: tightened OTA UUID matching, strictly validated service context, added active pairing polling, resynchronized stream framing in `on_notify`, enforced atomic write cap, hardened personal data redaction, made CLI `--address`/`--name` mutually exclusive, and added 6 unit test suites in `tests/test_c900_probe.py`.

