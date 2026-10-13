# Live session 1: read-only first contact from the owner's Mac (DRAFT)

**STATUS: DRAFT, NOT APPROVED.** Written 2026-10-13 in DEEP-PASS-1. Nothing here has been run. It runs only after the owner (a) says live work is necessary (INVARIANTS I-51) and (b) ticks the go/no-go list in section 2 and records the go-ahead in OPEN-QUESTIONS. Session 2 (writes) is a separate session with its own approval (section 9); passing session 1 does not approve it.

Sources: `HW-0-RUNSHEET.md` (HW-2, HW-3), `PROBE-GUIDE.md`, `docs/guides/PROBE-SECURITY.md`, `tools/c900_probe.py` as of DEEP-PASS-1, PROTOCOL sections 2-4 and 7, INVARIANTS I-13/I-14/I-30/I-35/I-51/I-54.

Who does what: every step marked **[human]** needs the owner and the watch. Nothing in this file can be done by an AI alone, and an AI must never write a result for a step that did not run.

## 0. What this session answers, and what it does not
| Question | Answered by | Tag after the run |
|---|---|---|
| Q01 advertised name | step 3 scan table | [H] |
| Q01 MAC + `12 34` in the scan record | only partly: bleak shows parsed manufacturer data, not the raw record | [H] if visible, else stays open (capture or PacketLogger) |
| Q02 GATT services | step 4 `SERVICE` lines | [H] |
| PROTOCOL_VERSION (the `ver` byte, 0-based index 5; I-10 calls it "byte 4"), from the 0x2A27 major | step 4 `READ 2a27 ... protocol_major=` | [H] |
| Feature map bytes (b1 0x80, b15 0x40, b18 0x20, b25 0x80) | step 4 `READ features ... hex=` | [H] |
| Q03 does the watch ask to bond | only if it volunteers (pairing dialog or 0x0C/19, 0x0E/1 frame) | [H] "seen" or "not seen in 30 s of idle listen" |
| Watch ack bytes, which keys it acks | **not answered** (no writes) | stays [U]; session 2 or capture |

## 1. If the owner's HCI capture arrives first
Run NEXT-STEPS section 4 (capture decision tree) first, then come back here and strike every row in section 0 that the capture settled. Section 4b of NEXT-STEPS says which steps of this session remain. If the capture settles Q01, Q02, the version byte, the feature map and Q03, this session is **skipped** and the next live step is session 2 at the earliest.

## 2. Go / no-go checklist (owner ticks all before step 1)
- [ ] Owner wrote "live work is necessary" for this session in OPEN-QUESTIONS (date, scope = LIVE-SESSION-1 only).
- [ ] Capture status checked (section 1): either no capture, or the capture left at least one row of section 0 open.
- [ ] Checkout is `feat/c900-hiwear-plus` at the DEEP-PASS-1 commit or later; `python3 -m unittest tests.test_c900_probe` passes on the Mac.
- [ ] Python is 3.10 or newer and is **not** the Xcode / Command Line Tools Python 3.9 (bleak 3.0.2 needs 3.10+). `python3 --version` printed.
- [ ] Probe dependencies installed with hashes in a venv (PROBE-GUIDE section 1); pip printed no hash warning.
- [ ] Terminal app has Bluetooth permission (System Settings, Privacy and Security, Bluetooth).
- [ ] Watch charged above 50 %, still bound to Hiwear Plus (do **not** unbind), showing its normal face.
- [ ] Phone Bluetooth **off** (or Hiwear Plus force-stopped). No other app or Mac connects to the watch.
- [ ] (2026-10-13: currently FAILS, the Mac is paired over Classic as `Watch Ultra`; see results/LIVE-PREFLIGHT-REVIEW.md section 4 for the owner's options.) The Mac has never been paired with the watch (System Settings, Bluetooth, the watch is not in "My Devices"). If it is, stop: write that down and ask; do not remove it.
- [ ] 30 minutes free; the owner stays at the Mac for the whole session.

No-go if any box is unticked.

## 3. Budget (counts everything, retries included)
| Item | Limit | Probe enforces |
|---|---|---|
| Scans | 2 (one retry) | no (owner counts) |
| Connections | 2 (one inspect, one retry inspect) | 3 per process cap, the run sheet is stricter |
| GATT characteristic writes | **0** | yes (inspect has no write path) |
| Descriptor writes | 1 per connection: the CCCD on `...DCCA9F` / `0003` | yes |
| Characteristic reads | 7 per connection (0x2A24, 0x2A25, 0x2A26, 0x2A27, 0x2A28, 0x2A29, 0x2A19) | fixed list |
| Listen | 30 s first run; a second run may use 120 s only if the first was clean | `--listen` max 150 |
| Wall clock | 30 min session; 180 s per probe process | probe: 180 s |

Note: HW-0-RUNSHEET counted 6 reads over 3 connections; the probe reads 7 in one connection. This sheet supersedes HW-0 for a Mac run.

## 4. Abort triggers (stop at once, Ctrl-C if the probe is still running, then record)
1. **Any macOS pairing or "Connection Request" dialog.** Press **Cancel** (never Pair or Connect), then Ctrl-C. On macOS the probe cannot see bond state (bleak 3.0.2 exposes none; the log says `pairing detection unavailable`), so this trigger depends on the owner's eyes. CoreBluetooth starts pairing by itself when a read hits a characteristic that needs encryption.
2. A pairing or confirmation prompt **on the watch**: do not confirm; Ctrl-C.
3. `SAFETY_STOP` in the output, for any reason.
4. More than 2 disconnects in the session.
5. Any OTA, update, "upgrading", or unusual screen on the watch; the watch reboots, loses time, face, or binding.
6. Output names 0xFF00, 0x18A8 or `...DCCA9E` as subscribed, written or read (the probe refuses this; seeing it means a bug).
7. Budget reached.
8. The phone reconnects (Hiwear Plus shows "connected").

After an abort: no further step in this session. The next session needs a new go-ahead.

## 5. Steps (all [human], on the Mac, in the reWatch checkout)
```bash
cd /path/to/reWatch
source .venv-probe/bin/activate
python3 --version                               # expect 3.10 or newer
python3 -m unittest tests.test_c900_probe       # expect OK
```

### Step 3: scan (read-only, no connect)
```bash
python tools/c900_probe.py scan --seconds 12
```
Expected:
- Log lines `SCAN device name=... rssi=... mac=xxxx...xxxx mfg=...` then `SCAN done count=N`. In the log, names of devices that do not contain `C900` or `Hiwear` show as `<redacted len=N>`, and manufacturer data shows company id, length and the first 2 bytes only.
- A screen-only table after `--- screen only, not logged ---` with full CoreBluetooth UUID addresses (on macOS these are per-Mac UUIDs, not MACs), every name, and full manufacturer bytes. **Do not tee or paste this table**; it holds third-party device names and possibly the watch's MAC.
- The C900's name is [U]. Pick the candidate by name and RSSI (move the watch close: strongest RSSI). If no candidate: one retry scan with the watch next to the Mac. Still none: stop, record "watch not advertising while bound with phone BT off" (that is a result, Q01).

Record (masked): candidate name, RSSI, manufacturer company id and length; whether the screen table's manufacturer bytes contain a 6-byte run followed by `12 34` (write only "yes at offset N" or "no", never the bytes).

### Step 4: inspect (connect, list, read, listen 30 s; one CCCD write)
```bash
python tools/c900_probe.py inspect --address <UUID from the screen table> --listen 30
```
Do not use `--name` on this first run; the address from the scan is exact.

During the 30 s listen: press the watch button once, open heart rate on the watch, raise the wrist. Do not touch any update or settings screen.

Expected, in order:
1. `INSPECT connect mac=xxxx...xxxx listen=30s`
2. `NOTE pairing detection unavailable on this BLE stack; ...` (normal on macOS; this is why abort trigger 1 matters).
3. `LAYOUT ok command-service present; ota_services_seen=N (untouched)`. N is 0 to 3 [C: up to three OTA services exist in the app, PROTOCOL section 2].
4. `SERVICE ...` lines: expect `6e400001-...-e50e24dcca9f` with `...0002[write-without-response...]` and `...0003[notify...]`, 0x180F, 0x180A, maybe 0xFF00 / 0x18A8 / `...dcca9e` (listed only).
5. `READ 2a24 ...`, `READ 2a25 value=<redacted len=N>` (possible serial), `READ 2a26 value=<firmware>`, `READ 2a27 value=<hw> protocol_major=<n>`, `READ features marker=0xaa len=... bits=... hex=...`, `READ 2a29 ...`, `READ battery=NN%`. A `READ xxxx error=...` line is a result, not a failure (the characteristic may not exist).
6. `LISTEN start uuid=...e50e24dcca9f seconds=30 (CCCD write is the only write)`
7. Zero or more `RX ...` lines. Likely none: the app starts traffic with bind (cmd 3), which the probe does not send [I].
8. `LISTEN done frames=N`, `DISCONNECT ok`, `PROBE_END`, `log: captures/c900-probe-inspect-....log`.

Deviation table:
| Seen | Do |
|---|---|
| `SAFETY_STOP unexpected service layout` | Stop. Q02 answer is "no NUS command service"; record the `SERVICE` lines; FACTS conflict; no session 2 until reviewed |
| `SAFETY_STOP ... command characteristic on OTA service` or `exactly one write and one notify` | Stop. Record; this is a layout surprise, not a probe bug |
| `marker` not `0xaa` | Continue; record (the app would then ask cmd 0x19, which we do not send) |
| `protocol_major` not 1 | Continue; record. Session 2 is blocked by the probe until the codec takes the version as input |
| `ABORT bond-trigger inbound` | Expected abort, a Q03 answer: record cmd/key and time; stop the session |
| `SAFETY_STOP inbound flood` | Stop; record; the watch streamed more than 200 frames or 64 KiB |
| `RX cmd=... ` not in PROTOCOL section 7 | Record raw line; never reply |
| Connect error / `ERROR ...` | One retry inspect (counts toward the budget). Second failure: stop and record |

Optional step 4b (only if step 4 was clean and the owner agrees): a second inspect with `--listen 120` to watch longer for bond triggers or unsolicited frames. Same expectations.

## 6. What to record (result file)
Write `targets/c900/tasks/results/LIVE-SESSION-1-<YYYY-MM-DD>.md` with:
- Date, time zone, Mac model, macOS version, Python version, checkout commit.
- Go/no-go ticks.
- For each step: command, exit code, and the masked log excerpt (the log lines only; never the screen table).
- The section 0 table filled with values and `[H]` tags, citing the log file name.
- Every abort trigger hit, with the time.
- Anything unexpected on the watch screen.

Masking rules: the probe log already masks addresses, redacts 0x2A25, and keeps third-party names out. Before sharing, the owner still searches the log for their own name, phone name, and any 12-character hex run, and removes them.

## 7. How to hand logs back
- Files: `captures/c900-probe-scan-*.log`, `captures/c900-probe-inspect-*.log` (git-ignored). Do not commit them.
- Send privately (direct message or an owner-controlled drive), not a public gist or issue.
- An agent then: reads the logs as untrusted data, writes the result file above with excerpts only, promotes `[H]` facts to FACTS/PROTOCOL with the result file as source, and updates OPEN-QUESTIONS Q01-Q03.

## 8. After the session
- Session clean and section 0 answered: the next live step is session 2, which needs its own approval.
- `protocol_major` != 1, no NUS, or a bond request seen: session 2 is blocked until the docs and code are reviewed for that result.

## 9. Session 2 (writes): separate, later, DRAFT
Runs only after session 1 (or a capture) has answered: services, `protocol_major == 1`, feature map, and "bond seen / not seen". Its own go-ahead is recorded in OPEN-QUESTIONS, naming the exact commands approved.

### 9.1 Why these writes and what they cost
| Command | Frame | Effect on the watch | Write cost [I] |
|---|---|---|---|
| `find` | cmd 2 key 11, payload `01` | watch vibrates / rings until stopped on the watch | no persistent state expected |
| `time` | cmd 2 key 1, packed local time | sets the clock | one settings write; the watch re-syncs time on every vendor-app connect anyway |
| `message` | cmd 2 key 18, type 1 (SMS), text `reWatch test` | one notification | may be stored in the watch's message list |
None of these is bind (cmd 3), which could displace the phone's binding; bind stays out of every probe session.

### 9.2 Go / no-go (owner ticks all)
- [ ] Session 1 result file exists and shows: NUS command service present, `protocol_major=1`, no bond request seen (or a reviewed plan for one).
- [ ] Owner approval names the commands, in order: `find`, then `time`, then `message` (each optional).
- [ ] Same environment ticks as section 2 (phone BT off, watch bound, Mac not paired, Python 3.10+, tests pass).
- [ ] The owner accepts that the watch may NAK or ignore these frames because the probe does not send bind first (the app binds before any setting, INVARIANTS I-35); an ack timeout is a result, not a reason to retry.
- [ ] The owner knows how to stop find on the watch.

### 9.3 Budget
| Item | Limit |
|---|---|
| Probe runs | 3 (one per command), no retries of the same command in the session |
| Connections | 1 per run |
| ATT writes | `find` 1, `time` 1, `message` 2 (24-byte frame in two 20-byte pieces); probe cap 5 per run |
| Reads | 1 per run (0x2A27 version check before writing) |
| Ack wait | 30 s per run (the app allows 100 s; a missing ack is recorded, not retried) |

### 9.4 Commands
```bash
python tools/c900_probe.py safe-write --address <UUID> --i-approve-writes --command find
# type: find
python tools/c900_probe.py safe-write --address <UUID> --i-approve-writes --command time
# type: time
python tools/c900_probe.py safe-write --address <UUID> --i-approve-writes --command message
# type: message
```
Expected per run: `READ 2a27 ... protocol_major=1`, `TX piece 1/1 len=10` (find) or `len=13` (time) or `TX piece 1/2 len=20`, `TX piece 2/2 len=4` (message), then either `ACK ok cmd=0x02 key=0x.. status=1 x=0x....` or `SAFETY_STOP ack timeout after 30s` or `SAFETY_STOP ack status=0`.

### 9.5 Abort triggers
All of section 4, plus: `SAFETY_STOP unexpected ack`, `ack status=...`, any inbound bond trigger, the watch shows anything other than the expected effect, the time on the watch is wrong after `time` (record the shown time; do not resend).

### 9.6 Record
Per run: the ack bytes the probe logged (cmd, key, status, x), the watch's visible effect, and the time to ack. These settle FACTS "watch ack bytes 6-7" (I-18) and "which cmd 2 keys the C900 acks" as [H].

### 9.7 Update 2026-10-13 (after C900-Q19 and the codec change)
- The probe now sends `ver = 0x10` on this watch (derived from 0x2A27 like the app); expect `READ 2a27 value=10000 protocol_major=10000 ver_byte=0x10`.
- Expected acks if the watch accepts without bind (unknown): `ACK ok ... x=0x000a x_is_frame_len=True` for find (10-byte frame), `x=0x000d` for time (13), `x=0x0018` for message (24). `x_is_frame_len=False` is a finding to record, not an abort.
- `time` is still last: on this watch feature b15 0x40 is set, and in C900-Q19 the phone tried to page the Classic address right after the time-sync ack. The probe never bonds, but record any dialog.
