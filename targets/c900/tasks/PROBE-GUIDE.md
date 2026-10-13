# Owner guide: probe your real C900 from a Mac

You will run `tools/c900_probe.py` on your Mac against your own C900. It is read-mostly; the only writes are one CCCD enable during `inspect`, and (only if you ask) one allowlisted command during `safe-write`. Read `docs/guides/PROBE-SECURITY.md` first.

**Do not unbind the watch from the Hiwear Plus app.** Just turn the phone's Bluetooth **off** so the app cannot connect while you probe.

## 1. One-time Mac setup
1. Install Python 3.10 or newer (`python3 --version`). The Python that ships with Xcode / Command Line Tools is 3.9 and will not install bleak 3.0.2; use python.org or Homebrew Python.
2. In the reWatch checkout:
   ```bash
   cd /path/to/reWatch
   python3 -m venv .venv-probe
   source .venv-probe/bin/activate
   python -m pip install --upgrade pip
   python -m pip install --require-hashes --only-binary=:all: -r requirements-probe.txt
   ```
   That installs bleak 3.0.2 and its macOS CoreBluetooth stack with pinned SHA-256 hashes. If pip complains about a hash, stop and tell us; do not `--no-deps` or skip hashes.
3. Grant **Bluetooth** permission to Terminal (or iTerm): System Settings → Privacy & Security → Bluetooth → enable your terminal app. On first scan macOS may prompt; accept.
4. Put the watch on its wrist or charger, charged above about 50%. Phone Bluetooth **off**.

## 2. Scan (read-only)
```bash
python tools/c900_probe.py scan --seconds 12
```
You get a screen-only table of nearby devices with full addresses. On macOS the address is a CoreBluetooth UUID such as `1A2B3C4D-....`, not a MAC. Copy the address of your C900. The log file masks addresses, keeps only names containing `C900` or `Hiwear`, and shortens manufacturer data; **do not tee or paste the screen table** (it shows other people's device names). Prefer `--address`; `--name 'Exact Name'` works only if exactly one device has that name.

## 3. Inspect (connect, read, listen; one CCCD write)
```bash
python tools/c900_probe.py inspect --address <address from the scan table> --listen 30
```
What it does:
- Connects **without** pairing. On macOS it prints `pairing detection unavailable`: macOS gives no bond state to apps, so if a pairing dialog appears, press **Cancel** and Ctrl-C yourself.
- Lists GATT services (OTA services may appear; they are not touched).
- Reads Device Information strings (0x2A25 is logged as `<redacted>`, it may be a serial), the version (`0x2A27`, printed as `protocol_major=`), the feature map (`0x2A28`, expects byte0 `0xAA`, logged with its hex), and battery (`0x2A19`).
- Enables notify **only** on the command characteristic `...DCCA9F` / `0003`, listens for `--listen` seconds, then disconnects.

What the output means:
- `LAYOUT ok` = command write/notify found.
- `READ features marker=0xaa ... bits={...}` = feature map; `isSupportPair` true means the vendor app would bond after time sync (the probe still will not).
- `RX cmd=...` / `RX ack=...` = something the watch sent on its own. Bond-trigger frames abort the session on purpose.
- `SAFETY_STOP ...` = a hard rule fired; nothing further is sent. Send us that log.

## 4. Safe-write (optional, one command, dual approval)
Only after a clean inspect. One command per run:
```bash
python tools/c900_probe.py safe-write --address <address> --i-approve-writes --command find
# or: --command time
# or: --command message   # sends the fixed text "reWatch test" as SMS type
```
You must pass `--i-approve-writes` **and** type the command name again at the prompt. Before writing, the probe reads 0x2A27 and refuses unless the version major is 1 (the app puts that number in every frame). It waits for an ack with status 1, then disconnects. Safe-write is live session 2 in `LIVE-SESSION-1.md` section 9 and needs its own approval. Any non-ok / unknown ack, bond-trigger, or pairing prompt aborts.

## 5. Abort conditions (automatic)
Pairing dialog (you press Cancel; macOS cannot report it to the probe) or bonding detected where the stack reports it; more than 2 disconnects; missing command service; any inbound bond-trigger (`0x0C` key 19 or `0x0E` key 1); write/connection/time caps exceeded; Ctrl-C. On abort the probe disconnects and writes `SAFETY_STOP` to the log.

## 6. Send us the log
Logs land in `captures/c900-probe-*.log` (git-ignored; `--log-dir` inside the repo must be under `captures/`). MACs are already masked and message text is redacted. Send that file privately (not a public gist). Do not commit it.

## 7. What not to do
- Do not unbind or factory-reset the watch.
- Do not run an OTA / watch-face / contacts transfer in the vendor app while probing.
- Do not edit `tools/c900_probe.py` to "just send one more command". Ask us instead.
