<!-- Imported 2026-10-13 from the removed combined target targets/t900-c900/PROTOCOL.md. Kept for history. C900 parts are SUPERSEDED: they assumed HryFine/HiWatch Pro and were written from a third-party write-up, not from the app. Current C900 facts: ../PROTOCOL.md and ../FACTS.md. -->

# Protocol: T900 and C900 watch

Every statement carries a tag: [C] [V] [H] [W] [I] [U]. Disputed values live in [FACTS.md](legacy-t900-c900-FACTS.md).

## 1. Transport selection
The client selects its wire transport dynamically during GATT service discovery, falling back to profile selection if multiple services are advertised:

| Transport | Identifier (UUID / Service) | Selected when | Tag |
|---|---|---|---|
| HryFine NUS Variant | Service `6E400001-B5A3-F393-E0A9-E50E24DCCA9F`<br>TX Char `6E400002-B5A3-F393-E0A9-E50E24DCCA9F`<br>RX Char `6E400003-B5A3-F393-E0A9-E50E24DCCA9F` | Advertised on C900 Ultra / C800 / BOOD watches paired with HryFine ecosystem | [W] |
| Standard Nordic NUS | Service `6E400001-B5A9-F393-E0A9-E50E24DCCA9E`<br>TX Char `6E400002-B5A9-F393-E0A9-E50E24DCCA9E`<br>RX Char `6E400003-B5A9-F393-E0A9-E50E24DCCA9E` | Standard Nordic UART fallback on certain Bluetrum/Nordic clone batches | [W] |
| JieLi RCSP | Service `0000AE00-0000-1000-8000-00805F9B34FB`<br>Write Char `0000AE01-0000-1000-8000-00805F9B34FB`<br>Notify Char `0000AE02-0000-1000-8000-00805F9B34FB` | Advertised on T800 / T900 Ultra series watches paired with HiWatch Pro | [W] |
| SIG Battery Service | Service `0x180F`, Char `0x2A19` (Battery Level) | Present on both C900 and T900 devices for passive status polling | [W] |
| SIG Device Info | Service `0x180A`, Chars `0x2A24` (Model), `0x2A26` (Firmware) | Present on both for static device identification | [W] |
| Prohibited OTA | Service `0x18A8` (Cus5610) / `0xAE10` / `0xAE20` | Blacklisted: writing triggers fatal bootloader bricking | [W], no primary source; kept blocked |
| Prohibited OTA (JieLi) | RCSP opcodes `0xE0`-`0xEF` on the normal `0xAE00` link | Refused by `build_jieli_frame` and by both links (`is_rcsp_ota_frame`) | 0xE5 [W] Jieli OTA SDK docs (device-pulled blocks); rest of range [I] |

## 2. Framing

### 2.1 HryFine / C900 Protocol Framing
All commands from app to watch follow the `0xDF` framing:

| Field | Offset | Length (bytes) | Type / Value | Description | Tag |
|---|---|---|---|---|---|
| Magic | 0 | 1 | `0xDF` | Frame start identifier | [W] |
| Len (High) | 1 | 1 | uint8 | Big-endian length high byte: `((TotalBytes - 4) >> 8)` | [W] |
| Len (Low) | 2 | 1 | uint8 | Big-endian length low byte: `((TotalBytes - 4) & 0xFF)` | [W] |
| Checksum | 3 | 1 | uint8 | Modulo-256 sum of all bytes in frame with byte 3 = 0x00 | [W] |
| Command | 4 | 1 | uint8 | Primary command opcode (e.g. 0x02, 0xF3, 0x05) | [W] |
| Key / Type | 5 | 1 | `0x01` | Protocol constant key identifier | [W] |
| Sub-command | 6 | 1 | uint8 | Sub-command opcode (e.g. 0x0A, 0x00, 0x01) | [W] |
| PayLen (High) | 7 | 1 | uint8 | Payload length high byte | [W] |
| PayLen (Low) | 8 | 1 | uint8 | Payload length low byte | [W] |
| Payload | 9 | Variable | bytes | Command arguments (parameters, text, timestamp) | [W] |

Watch to App Acknowledgement / Response Frame:
| Field | Offset | Length (bytes) | Type / Value | Description | Tag |
|---|---|---|---|---|---|
| Magic | 0 | 1 | `0xFD` | Acknowledgement start identifier | [W] |
| Len (High) | 1 | 1 | `0x00` | Big-endian length high byte (constant 0x00) | [W] |
| Len (Low) | 2 | 1 | `0x05` | Big-endian length low byte (constant 0x05) | [W] |
| Checksum | 3 | 1 | uint8 | Modulo-256 sum of all bytes with byte 3 = 0x00 | [W] |
| Command | 4 | 1 | uint8 | Echoed primary command opcode | [W] |
| Key | 5 | 1 | `0x01` | Protocol constant key identifier | [W] |
| AckLen (High) | 6 | 1 | `0x00` | Ack length high byte | [W] |
| AckLen (Low) | 7 | 1 | `0x01` | Ack length low byte | [W] |
| Status | 8 | 1 | uint8 | `0x01` = success / acknowledge, other = error | [W] |

### 2.2 JieLi / T900 RCSP Framing
All commands over service `0xAE00` follow standard JieLi RCSP framing:

| Field | Offset | Length (bytes) | Type / Value | Description | Tag |
|---|---|---|---|---|---|
| Magic | 0..2 | 3 | `0xFE 0xDC 0xBA` | RCSP frame synchronization header | [C] |
| Flag | 3 | 1 | uint8 | Bit 7: 1=app-to-device; Bit 6: 1=wants response; typical `0xC0` | [C] |
| Opcode | 4 | 1 | uint8 | Command opcode (0x01 data, 0x02 status, 0x1B file transfer) | [C] |
| Length | 5..6 | 2 | uint16 BE | Big-endian byte count of the body (`len(body)`) | [C] |
| Body | 7..End-1 | Variable | bytes | `sn(1)` + inner payload / parameters | [C] |
| Trailer | End | 1 | `0xEF` | Frame termination delimiter | [C] |

## 3. Checksums

### 3.1 HryFine Checksum Algorithm
- Name: Sum8 (Modulo-256 addition) [W]
- Algorithm: Set the checksum field byte[3] to 0x00, compute the arithmetic sum of all bytes in the complete frame modulo 256. Store the resulting byte in byte[3].
- Verification test vector:
  - Input: Frame with byte[3]=0x00: `DF 00 05 00 F3 01 00 00 00`
  - Sum: 223 + 0 + 5 + 0 + 243 + 1 + 0 + 0 + 0 = 472
  - Modulo 256: 472 % 256 = 216 = `0xD8`
  - Output: `DF 00 05 D8 F3 01 00 00 00` [V]

### 3.2 JieLi Checksums
- RCSP framing does not employ an inner byte checksum; frame boundaries are delimited by `FE DC BA` and `EF` [C].
- File and dial transfers employ standard CRC-16/XMODEM (polynomial 0x1021, init 0x0000, check value "123456789" = 0x31C3) [C, V].

## 4. Commands

### 4.1 HryFine / C900 Command Set
| Opcode | Sub | Direction | Parameters | Reply | Purpose | Tag |
|---|---|---|---|---|---|---|
| `0x02` | `0x0A` | App -> Watch | 7 bytes: `YYYY(2B BE) MM(1B) DD(1B) HH(1B) mm(1B) ss(1B)` | `0xFD` ACK (Cmd 0x02, Status 0x01) | Time synchronization | [W] |
| `0xF3` | `0x00` | App -> Watch | None (PayLen=0) | `0xFD` metadata frame or ACK | Query device info / version | [W] |
| `0x05` | `0x01` | App -> Watch | AppID(1B) + TitleLen(1B) + Title + MsgLen(1B) + Msg | `0xFD` ACK (Cmd 0x05, Status 0x01) | Push notification / alert | [W] |
| `0x07` | `0x01` | App -> Watch | Level(1B): `0x01` ring/vibrate, `0x00` stop | `0xFD` ACK | Find watch alert | [W] |
| `0x1A` | `0x01` | App -> Watch | Chunk offset(4B BE) + Chunk data | `0xFD` ACK (Cmd 0x1A, Status 0x01) | Watch face dial binary transfer | [I] |

### 4.2 JieLi / T900 Command Set
| Opcode | Direction | Parameters | Reply | Purpose | Tag |
|---|---|---|---|---|---|
| `0x02` | App -> Watch | `sn(1)` | Status response (battery, version, mode) | Read status | [C] |
| `0x21` | App -> Watch | `sn(1) + EnvParams` | Env prepared ACK | Prepare dial transfer environment | [C] |
| `0x1B` | App -> Watch | `sn(1) + Size(4B) + CRC16(2B) + Path` | Transfer ready ACK | Start large file dial transfer | [C] |
| `0x1C` | App -> Watch | `sn(1) + Reason(1B)` | Transfer finished ACK | Stop / finalize file transfer | [C] |

## 5. Session state machine
```
[Disconnected]
      |
      v  connectGatt() [Timeout: 10s]
[Connected]
      |
      v  discoverServices()
[Services Discovered]
      |
      +---> If 6E400001 (NUS):
      |         |
      |         v  enableNotifications(6E400003, CCCD 0x2902) [Timeout: 5s]
      |     [HryFine Ready]
      |         |
      |         +---> Query Status / Battery (Read 0x2A19 / Send 0xF3)
      |         +---> Time Sync (Send Cmd 0x02, Sub 0x0A)
      |         +---> Push Notification (Send Cmd 0x05, Sub 0x01)
      |         +---> Push Dial (Chunked transfer with safe-write guard)
      |
      +---> If 0000AE00 (JieLi RCSP):
                |
                v  enableNotifications(0xAE02, CCCD 0x2902) [Timeout: 5s]
            [JieLi Auth / Passive]
                |
                +---> Optional E1/SAFER+ Auth exchange (0x00 challenge, 0x01 response)
                +---> Query Status (Opcode 0x02)
                +---> Time Sync / Push Dial
```

Timeouts and retries:
- Connection timeout: 10 seconds (1 retry) [I]
- CCCD write notification acknowledge: 3 seconds [I]
- Command response wait: 2 seconds, max 2 retries before reporting packet loss [I]
- Safe-write interval between successive write packets: minimum 50 ms [I]

## 6. Transfers and containers: Watch Face Binary Structure

Watch face files (`.bin`) use uncompressed RGB565 little-endian pixels with coordinate widget tables:

### Header Format (32 bytes)
| Offset | Length | Type / Endian | Field | Description | Tag |
|---|---|---|---|---|---|
| 0x00 | 4 | ASCII | Magic | `0x44 0x49 0x41 0x4C` (`DIAL`) | [W] |
| 0x04 | 2 | uint16 LE | Version | Dial format version (`0x0001`) | [W] |
| 0x06 | 2 | uint16 LE | Width | Display horizontal resolution (e.g. 240 or 320) | [W] |
| 0x08 | 2 | uint16 LE | Height | Display vertical resolution (e.g. 286 or 385) | [W] |
| 0x0A | 2 | uint16 LE | ColorFormat | `0x0001` = RGB565 (16 bits per pixel) | [W] |
| 0x0C | 2 | uint16 LE | Flags | Bit 0: Has preview; Bit 1: Has custom coordinates | [W] |
| 0x0E | 2 | uint16 LE | Reserved | `0x0000` padding | [W] |
| 0x10 | 4 | uint32 LE | ThumbOffset | Byte offset to preview thumbnail (typical 32) | [W] |
| 0x14 | 4 | uint32 LE | ThumbSize | Byte length of preview thumbnail | [W] |
| 0x18 | 4 | uint32 LE | BackgroundOffset | Byte offset to main background image | [W] |
| 0x1C | 4 | uint32 LE | BackgroundSize | Byte length of background: `Width * Height * 2` | [W] |

Color Encoding:
- RGB565 format: 16 bits per pixel, little-endian:
  `RGB565 = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)`
  `Byte0 = RGB565 & 0xFF`, `Byte1 = (RGB565 >> 8) & 0xFF` [V]

## 7. Worked examples

### Example 1: HryFine Metadata Query
Formula: `DF 00 05 [Sum8] F3 01 00 00 00`
Sum calculation: `(223 + 0 + 5 + 0 + 243 + 1 + 0 + 0 + 0) % 256 = 216 (0xD8)`
Wire bytes:
```hex
DF 00 05 D8 F3 01 00 00 00
```
Tag: [V]

### Example 2: HryFine Time Sync (2026-10-12 09:30:00)
Parameters: Year=2026 (0x07EA), Month=10 (0x0A), Day=12 (0x0C), Hour=9 (0x09), Minute=30 (0x1E), Second=0 (0x00).
Inner length: 12 bytes (`0x00 0x0C`).
Sum calculation: `(223 + 0 + 12 + 0 + 2 + 1 + 10 + 0 + 7 + 7 + 234 + 10 + 12 + 9 + 30 + 0) % 256 = 45 (0x2D)`
Wire bytes:
```hex
DF 00 0C 2D 02 01 0A 00 07 07 EA 0A 0C 09 1E 00
```
Tag: [V]

### Example 3: HryFine Notification Alert (SMS: "Alert", "Test")
Inner length: 17 bytes (`0x00 0x11`).
Sum calculation: `1189 % 256 = 165 (0xA5)`
Wire bytes:
```hex
DF 00 11 A5 05 01 01 00 0C 01 05 41 6C 65 72 74 04 54 65 73 74
```
Tag: [V]

### Example 4: JieLi RCSP Status Read
Header: `FE DC BA`, Flag: `0xC0`, Opcode: `0x02`, Len: `0x00 0x01`, Body: `0x01` (sn=1), Trailer: `EF`.
Wire bytes:
```hex
FE DC BA C0 02 00 01 01 EF
```
Tag: [V]

## 8. Per-model differences
| Model Profile | Primary SoC | Transport | Display Resolution | Default App | Tag |
|---|---|---|---|---|---|
| C900 Ultra | Bluetrum AB53xx / AB56xx | HryFine NUS (`...DCCA9F`) | 240x286 | HryFine | [W] |
| C900 Pro Max | Bluetrum / JieLi hybrid | HryFine NUS (`...DCCA9F` / `...DCCA9E`) | 320x385 | HryFine | [W] |
| T900 Ultra | JieLi JL7012 / AC6954 | JieLi RCSP (`0xAE00`) | 240x286 | HiWatch Pro | [W] |
| T900 Ultra 2 | JieLi JL7012F6 | JieLi RCSP (`0xAE00`) | 320x385 | HiWatch Pro | [W] |

## 9. Unknowns and the test that settles each
| Unknown | Why it matters | Test |
|---|---|---|
| C900 NUS UUID variant (`0x9F` vs `0x9E`) | Device will not connect if UUID differs | Run read-only BLE probe (`reWatch probe --scan`); check discovered characteristic UUID against both profiles |
| T900 Authentication Requirement | Handshake deadlock if firmware enforces E1/SAFER+ | Connect in read-only mode and check if 0xAE02 pushes unprompted auth challenge within 2 seconds |
| Watch Face Chunk Size Limit | Buffer overflow or dropped packets during dial transfer | Test transfer in 20-byte, 128-byte, and 240-byte chunks on real hardware |
