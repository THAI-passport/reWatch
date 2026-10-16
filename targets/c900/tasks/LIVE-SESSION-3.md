# Live session 3: `message`, then `time` (APPROVED 2026-10-13, owner runs it)

Approval: OPEN-QUESTIONS "Owner approvals 2026-10-13 (evening)". Same environment rules as LIVE-SESSION-1 section 2 (phone Bluetooth off, watch bound to Hiwear Plus, Terminal with Bluetooth permission, tests pass). An AI never runs these commands.

## Budget
| Run | ATT writes | Reads | Connections |
|---|---|---|---|
| message | 2 (24-byte frame, two pieces) | 1 (0x2A27) | 1 |
| time | 1 (13-byte frame) | 1 | 1 |
No retries. A timeout or NAK is a result.

## Commands (Mac Terminal, in the reWatch checkout, venv active)
```bash
python3 -m unittest tests.test_c900_probe
python tools/c900_probe.py safe-write --address <CB-UUID from scan> --i-approve-writes --command message
#   type: message
python tools/c900_probe.py safe-write --address <CB-UUID from scan> --i-approve-writes --command time
#   type: time
```

## Expected
| Run | Log lines | Watch |
|---|---|---|
| message | `READ 2a27 value=10000 ... ver_byte=0x10`, `TX piece 1/2 len=20`, `TX piece 2/2 len=4`, `ACK ok cmd=0x02 key=0x12 status=1 x=0x0018 x_is_frame_len=True` | an SMS-style notification with the text `reWatch test` [I: the app sends "title:body"; without a colon the watch may show it as title only] |
| time | `TX piece 1/1 len=13`, `ACK ok cmd=0x02 key=0x01 status=1 x=0x000d x_is_frame_len=True` | clock shows the Mac's local time (seconds may differ) |

## Abort and watch-outs
- All LIVE-SESSION-1 section 4 triggers.
- `time`: in C900-Q19 the phone tried Classic pairing right after this ack because feature b15 0x40 is set. The probe never pairs; if macOS shows any pairing or "Connection Request" dialog, press Cancel, then Ctrl-C, and record it.
- `x_is_frame_len=False`, `ack status=0`, or `unexpected ack`: record the line; no retry.
- Message split into 2 pieces: if only the first piece arrives the watch gets a short frame; expect an ack timeout rather than a wrong action. Record.

## Record
`tasks/results/LIVE-SESSION-3-<date>.md`: masked log lines (skill re-privacy-scrub), what the watch showed, any dialog. Then `python3 tools/privacy_scan.py <file> --strict`, tests, lint, push `feat/c900-hiwear-plus`.
