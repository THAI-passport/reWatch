# Live Session 2 Results: Safe-Write Find Command (2026-10-13)

Date: 2026-10-13 (Asia/Saigon)  
Target: C900 / Watch Ultra (`targets/c900`)  
Branch: `feat/c900-hiwear-plus`  
Operator: Human owner via interactive macOS Terminal  
Environment: macOS (Darwin 25F84 / macOS 26.5.2), Python 3.13.5 (`.venv-probe`), bleak 3.0.2  
Logs cited:
- Aborted attempt: `captures/c900-probe-safe-write-20261013-180232.log` (confirmation mismatch)
- Successful run: `captures/c900-probe-safe-write-20261013-180245.log`

---

## 1. Questions Settled by Live Session 2

| Question / Item | Value / Finding | Evidence Tag | Source |
|---|---|---|---|
| **Find Command Acceptance** | Watch accepts and executes `find` (`cmd=0x02 key=0x0B`, payload `0x01`) without prior bind handshake (cmd 3 key 0) | [H] | Probe log line 7; watch screen displayed "the bracelet has been found!" with vibration [H owner] |
| **Version Byte on the Wire** | Derived `ver_byte=0x10` from 0x2A27 (`10000`) verified on live transmission; accepted by watch without NAK | [H] | Probe log line 5 |
| **TX Framing & Piece Count** | Single 10-byte piece transmitted (`TX piece 1/1 len=10`) without fragmentation | [H] | Probe log line 6 |
| **Watch ACK Format** | Immediate ACK received: `ACK ok cmd=0x02 key=0x0b status=1 x=0x000a x_is_frame_len=True` within < 1 s | [H] | Probe log line 7 |
| **ACK Field `x` Meaning** | `x = 0x000A` (10 decimal), exactly matching the total 10-byte frame length. Confirms invariant I-18 on direct probe write | [H] | Probe log line 7 |
| **Prior Bind Prerequisite** | Device does not require binding or authentication prior to processing `find` alerts | [H] | Narrowed I-35: bind is not a hardware gate for alert commands |
| **Abort Triggers** | 0 abort triggers hit during execution; clean disconnect | [H] | Probe log lines 8-9 |

---

## 2. Pre-flight and Authorization Verification

- [x] Owner recorded explicit written approval in `targets/c900/OPEN-QUESTIONS.md` for `find` safe-write.
- [x] Pre-flight verification passed: 177 unit tests pass, `rw.py lint` reported 0 problems.
- [x] Interactive fail-safe verification: first run typed `j` instead of `find`, triggering immediate `SAFETY_STOP confirmation mismatch; nothing sent` (exit code 3). Proves confirmation safety gate functions as designed.
- [x] Budget respected: 1 connection, 1 GATT read (0x2A27), 1 GATT write (1 piece of 10 bytes), ACK received immediately (< 1 s, well within 30 s cap).

---

## 3. Step Details and Scrubbed Logs

### 3.1 Initial Run (Aborted by Confirmation Gate)

Command executed by owner:
```bash
.venv-probe/bin/python tools/c900_probe.py safe-write --address <CB-UUID masked> --i-approve-writes --command find
```

Exit code: `3`

Masked log excerpt (`captures/c900-probe-safe-write-20261013-180232.log`):
```text
2026-10-13T18:02:32 PROBE_START mode=safe-write
2026-10-13T18:02:32 preflight bluetooth authorization=3
Type the command name 'find' to confirm sending ONE allowlisted frame (cmd=0x02 key=0x0b, 10 bytes), or anything else to abort: j
2026-10-13T18:02:36 SAFETY_STOP confirmation mismatch; nothing sent
2026-10-13T18:02:36 PROBE_END
```

### 3.2 Second Run (Successful Execution)

Command executed by owner:
```bash
.venv-probe/bin/python tools/c900_probe.py safe-write --address <CB-UUID masked> --i-approve-writes --command find
```

Exit code: `0`

Masked log excerpt (`captures/c900-probe-safe-write-20261013-180245.log`):
```text
2026-10-13T18:02:45 PROBE_START mode=safe-write
2026-10-13T18:02:45 preflight bluetooth authorization=3
Type the command name 'find' to confirm sending ONE allowlisted frame (cmd=0x02 key=0x0b, 10 bytes), or anything else to abort: find
2026-10-13T18:03:19 SAFE_WRITE connect mac=5301...712B command=find
2026-10-13T18:03:21 NOTE pairing detection unavailable on this BLE stack; if the OS shows a pairing dialog press Cancel, then Ctrl-C
2026-10-13T18:03:21 READ 2a27 value=10000 protocol_major=10000 ver_byte=0x10
2026-10-13T18:03:21 TX piece 1/1 len=10
2026-10-13T18:03:21 ACK ok cmd=0x02 key=0x0b status=1 x=0x000a x_is_frame_len=True
2026-10-13T18:03:21 DISCONNECT ok
2026-10-13T18:03:21 PROBE_END
```

Physical device observation:
- Watch screen displayed: "the bracelet has been found!" [H owner].
- Watch vibrated upon receipt of the frame [H owner].
- Normal watch face resumed after alert acknowledged on device [H owner].

---

## 4. Evaluation against Invariants and Protocol Specifications

1. **Version byte (`ver = 0x10`, I-10):**
   Confirmed on the wire. The probe read `"10000"` from `0x2A27`, converted it to `ver_byte = 0x10`, built the frame with `ver = 0x10`, and the watch accepted it immediately with `status=1`.
2. **ACK field `x` (I-18):**
   Confirmed on the wire. The frame sent was 10 bytes (`DF 00 05 <sum>` cmd=0x02 ver=0x10 key=0x0B plen=0x0001 payload=0x01). The watch replied with `x = 0x000A` (10 decimal), confirming `x_is_frame_len = True`.
3. **Bind prerequisite (I-35):**
   Narrowed. While the vendor app always executes bind (`cmd 0x03 key 0`) during initial synchronization, the C900 hardware firmware accepts and acts upon `find` (`cmd 0x02 key 0x0B`) over an unbound connection.

## Review note (Claude, 2026-10-13)
Precise scope of the bind finding: the watch was still bound to the phone's Hiwear Plus; this BLE session sent no bind (cmd 3) of its own and the watch executed `find`. So "no per-connection bind needed for cmd 2 key 11 while the watch is bound elsewhere" [H]. Not yet shown: behaviour on a watch with no binding at all, and any other command (time, message, settings). "Bind is not a hardware gate for alert commands" generalises from one command; read it as find only.
