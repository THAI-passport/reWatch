# reWatch

A workflow for reverse engineering smartwatch and band companion apps so an open, local-only client can talk to the watch. Software first (the app, its libraries, public documentation, existing captures), hardware only as a last resort and only with the owner's explicit approval. Give an agent one line, get back a protocol spec, an open client, a software simulator, tests, and an honest list of what only real hardware can settle.

Seeded from reWork, which was distilled from the reBeamBox project (a BLE e-badge); see docs/FROM-REBEAMBOX.md for what was carried over. Generic procedure and tool tricks: docs/SOP.md.

## One-go start
Open this repo in Claude Code (or any agent that reads `AGENTS.md`), and prompt:

```
Reverse engineer: <watch or app name(s)>.   Goal: <what the client must do>.
```
The agent reads `AGENTS.md`, loads the `re-workflow` skill, and runs gates G0 to G5 without asking for approval between them. A benchmark prompt with pass criteria is in `targets/_benchmark/BENCHMARK.md`.

## What is inside
| Path | Purpose |
|---|---|
| `AGENTS.md` | Contract: prompt format, ground rules, logs, platform and live-contact rules, workflow, evidence tags, gates |
| `docs/SOP.md` | Generic procedure, tool tricks and lessons; updated after each pass |
| `docs/FROM-REBEAMBOX.md` | What was carried over from the worked example, what was left |
| `FIXES.md` | Open and fixed issues in reWatch itself |
| `CLAUDE.md` | Imports AGENTS.md for Claude Code |
| `.claude/skills/re-workflow` | Orchestrator, entry point; loads the other skills when relevant |
| `.claude/skills/re-acquire` | Hardware name to app, download, validate, hash |
| `.claude/skills/re-static` | jadx/apktool survey, surface map, obfuscation, decompiler failures |
| `.claude/skills/re-protocol-spec` | Byte-exact spec, checksums, SDK command layers, captures |
| `.claude/skills/re-native-emulation` | `.so` recovery with capstone and unicorn |
| `.claude/skills/re-client-sim` | Layered client, simulator, dry-run, safe-write, fixtures, CI |
| `.claude/skills/re-watch-targets` | Watch specifics: stacks, standard GATT services, features, watch face and OTA shapes, read-only safe probes, what to record per family |
| `.claude/skills/re-ble-android-patterns` | Finding transports in decompiled Android code: GATT, MTU, write types, scan filters, name dispatch, catalogs, ACK patterns, Wi-Fi modes |
| `.claude/skills/re-jieli` | Jieli chip family: recognition, RCSP frames, E1/SAFER+ auth, large-file transfer, FatFS, OTA awareness, emulation |
| `.claude/skills/re-capture-ingestion` | HCI snoop and pcap workflow with `tools/btcap.py` |
| `.claude/skills/re-hardware-recon` | First contact with a real device, write budget, task packs for weaker agents, gated teardown |
| `docs/recon/budget-smartwatch-landscape.md` | Imported third-party landscape of T900/C900-class watches (all `[W]`, with a flaws table) |
| `docs/NEXT-PASS-PROMPT.md` | Prompt for an agent pass over reBeamBox, reWork and reWatch |
| `templates/` | TARGET, SOURCES, FACTS, PROTOCOL, LOG, HANDOFF |
| `tools/rw.py` | `init`, `doctor`, `hash`, `recon`, `lint` (stdlib only) |
| `tools/btcap.py` | btsnoop/pcap/pcapng to ATT write/notify table by UUID |
| `tools/c900_decode.py` | C900 DF/FD frame decoder over a capture or btcap JSON: reassembly, sum check, cmd/key labels, feature bits, bond-trigger/blocked-cmd/OTA flags. Decode only |
| `tools/crcfind.py` | Identify a CRC from sample frames |
| `tools/notify_log.py` | Passive BLE notification logger (touch/event discovery); OTA/DFU deny list always on, `--only UUID` to pin one characteristic |
| `tools/make_test_media.py` | Synthetic test images, GIF and clips for display devices |
| `templates/tasks/` | Recon task pack copied into every target by `init` |
| `tools/setup_tools.py` | User-space JDK, jadx, apktool, venv (no admin rights); Linux, macOS, Windows. `setup-tools.sh` wraps it |
| `tools/recover-failed-methods.sh` | Second-chance decompile via simple mode and CFR |
| `tools/rebuild_analysis.py` | Rebuild a target's artifacts and jadx tree from SOURCES: hash-verified, idempotent, `--dry-run`, `--max-heap`, `--url`; Linux, macOS, Windows. `rebuild-analysis.sh` wraps it |

## Manual quick start
```
python tools/setup_tools.py
# If a target uses a pinned REPO_COPY under resources/: install Git LFS, then `git lfs install && git lfs pull`        # once; optional --emulation (Windows: run it from PowerShell)
python tools/rw.py doctor
python tools/rw.py init mywatch --name "My watch" --goal "sync status from CLI"
python tools/rw.py hash targets/mywatch/artifacts/app.xapk --slug mywatch
python tools/rw.py recon targets/mywatch/decompiled --slug mywatch
python tools/rw.py lint
python -m unittest discover -s tests
```

## Scope and limits
Static analysis first, interoperability, local clients. It does not install or run target apps, does not ship vendor code, and does not defeat protection mechanisms. Results from simulators are consistency checks, never hardware truth.
