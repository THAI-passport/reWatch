# Owner guide: probe your real C900 from a Mac

You will run `tools/c900_probe.py` on your Mac against your own C900. It is read-mostly; the only writes are one CCCD enable during `inspect`, and (only if you ask) one allowlisted command during `safe-write`. Read `docs/guides/PROBE-SECURITY.md` first.

**Do not unbind the watch from the Hiwear Plus app.** Just turn the phone's Bluetooth **off** so the app cannot connect while you probe.

## 1. One-time Mac setup
1. Install a recent Python 3.10+ (`python3 --version`).
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
You get a table of nearby devices with full addresses (the log file masks them). Copy the address of your C900. If the name is unique you may use `--name 'Exact Name'` later instead.

## 3. Inspect (connect, read, listen; one CCCD write)
```bash
python tools/c900_probe.py inspect --address AA:BB:CC:DD:EE:FF --listen 30
```
What it does:
- Connects **without** pairing.
- Lists GATT services (OTA services may appear; they are not touched).
- Reads Device Information strings, the feature map (`0x2A28`, expects byte0 `0xAA`), and battery (`0x2A19`).
- Enables notify **only** on the command characteristic `...DCCA9F` / `0003`, listens for `--listen` seconds, then disconnects.

What the output means:
- `LAYOUT ok` = command write/notify found.
- `READ features marker=0xaa ... bits={...}` = feature map; `isSupportPair` true means the vendor app would bond after time sync (the probe still will not).
- `RX cmd=...` / `RX ack=...` = something the watch sent on its own. Bond-trigger frames abort the session on purpose.
- `SAFETY_STOP ...` = a hard rule fired; nothing further is sent. Send us that log.

## 4. Safe-write (optional, one command, dual approval)
Only after a clean inspect. One command per run:
```bash
python tools/c900_probe.py safe-write --address AA:BB:CC:DD:EE:FF --i-approve-writes --command find
# or: --command time
# or: --command message   # sends the fixed text "reWatch test" as SMS type
```
You must pass `--i-approve-writes` **and** type the command name again at the prompt. The probe waits for an ack with status 1, then disconnects. Any non-ok / unknown ack, bond-trigger, or pairing prompt aborts.

## 5. Abort conditions (automatic)
Pairing dialog / bonding detected; more than 2 disconnects; missing command service; any inbound bond-trigger (`0x0C` key 19 or `0x0E` key 1); write/connection/time caps exceeded; Ctrl-C. On abort the probe disconnects and writes `SAFETY_STOP` to the log.

## 6. Send us the log
Logs land in `captures/c900-probe-*.log` (git-ignored). MACs are already masked and message text is redacted. Send that file privately (not a public gist). Do not commit it.

## 7. What not to do
- Do not unbind or factory-reset the watch.
- Do not run an OTA / watch-face / contacts transfer in the vendor app while probing.
- Do not edit `tools/c900_probe.py` to "just send one more command". Ask us instead.
