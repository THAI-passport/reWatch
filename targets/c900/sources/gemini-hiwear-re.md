<!-- Third-party document supplied by the owner on 2026-10-13 (written with Gemini). Untrusted data, kept verbatim below this note. Every claim is [W] unless FACTS.md section 2 says it was confirmed in the Hiwear Plus 2.0.1 code. Several opcodes in it are wrong and two are destructive (0x04 = unbind, 0x07 = factory test). Do not build from it. -->

# Hiwear Plus & C900 Smartwatch Reverse Engineering Technical Reference

Audience: Embedded engineers, reverse engineers, and clean-room client architects.  
Target Repository: `reWatch` (clean-room companion client for budget smartwatches).  
Target Device: C900 Ultra / Pro Max (Apple Watch Ultra clone, ~120–250 THB tier).  
Companion Target App: **Hiwear Plus** (`com.myled.HiwearPlus`), Android version 2.0.x / 1.1.x.  
Evidence Taxonomy: `[C]` Confirmed via decompilation/code, `[I]` Inferred logic, `[W]` Third-party reported from hardware/captures, `[U]` Unknown pending empirical capture.

---

## 1. Executive Summary & Ecosystem Provenance

### 1.1 The White-Label Lineage: "Hiwear" is United Power
The app **Hiwear Plus** (`com.myled.HiwearPlus`) is published by **Shenzhen United Power Technology Co., Ltd.** (深圳市联合之力科技有限公司, commonly referred to in Chinese codebases as **`lianhezhuli`**).

```
+---------------------------------------------------------------+
|         Shenzhen United Power Technology Co., Ltd.            |
|                   (联合之力 / lianhezhuli)                    |
|      Core Wearable SDK, BLE Protocol Stack, Dial Builder      |
+---------------------------------------------------------------+
                               |
         +---------------------+---------------------+
         |                     |                     |
         v                     v                     v
      HryFine             Hiwear Plus             Laxasfit / M2Wear
(com.lianhezhuli.hyfit) (com.myled.HiwearPlus)  (com.lianhezhuli.laxasfit)
         |                     |                     |
         +---------------------+---------------------+
                               |
                               v
           Identical Wire Protocol: 0xDF / 0xFD Framing
           Targeting Bluetrum (AB56xx) & JieLi (JL7012)
```

* **SDK Identity:** `Hiwear Plus` is not an independent application; it is a branded white-label reskin of the core **HryFine** engine.
* **Engineering Impact:** You do not have to start from scratch. The wire protocol, GATT UUID layout, notification framing, and dial format in `Hiwear Plus` directly match the `HryFine` (`0xDF`/`0xFD`) protocol specification reverse-engineered in community teardowns.
* **Scope Objective for `reWatch`:** Replace `com.myled.HiwearPlus` with an offline, telemetry-free Python CLI and Web Bluetooth interface to pair, sync clock time, set alarms, send notifications, and push custom watch faces.

---

## 2. Silicon Family & Hardware Architecture of the C900

Unlike the T900 Ultra (which almost exclusively ships with Zhuhai JieLi SoCs), the C900 Ultra series commonly runs on **Shenzhen Bluetrum Technology (中科蓝讯)** silicon.

### 2.1 Microcontroller Specifications
* **Primary Processor:** **Bluetrum AB5610B / AB56xx series** or **BT8958B** ("Xunlong Generation 3" smartwatch platform) `[W]`.
* **CPU Core:** 32-bit **RISC-V core** (RV32IMAC instruction set architecture) running at 120 MHz to 160 MHz `[W]`.
* **Memory & Storage:**
  * Internal SRAM: 192 KB to 256 KB.
  * External Non-Volatile Storage: 32 Mbit to 64 Mbit (4 MB to 8 MB) SPI NOR Flash located on GPIO bus G `[W]`.
* **Radio Baseband:** Dual-Mode Bluetooth 5.3:
  * **BLE Controller:** Handles GATT data synchronization (time, settings, watch face upload).
  * **BR/EDR Classic Audio Baseband:** Handles watch calling (HFP/HSP) and wrist audio streaming (A2DP).

### 2.2 Physical Compartment & Sensor Reality
* **Chassis Construction:** Dense zinc-aluminum alloy mid-frame, tempered mineral glass lens, real corner chassis screws, and spring-loaded strap latches (mechanically superior to the pot-metal T-series).
* **Display Subsystem:** 2.02"–2.09" IPS LCD panel ($240 \times 286$ or $320 \times 385$ pixels), 8-bit MCU parallel interface or 4-wire SPI with CST816 capacitive touch IC.
* **The Biometric Illusion:** The rear green LEDs (SMD 0805) and phototransistor are driven by firmware timer loops. Blood pressure, SpO2, and heart rate readings are synthetic numbers generated in software. **Exclude biometric ingestion from `reWatch`.**

---

## 3. APK Decomposition & Triage Strategy

### 3.1 Package Metadata & Artifacts
* **Package Name:** `com.myled.HiwearPlus`
* **Distribution Bundle:** Standard APK or XAPK (Split APK containing `base.apk` and `config.arm64_v8a`).
* **Permissions Profile:** Demands 36+ permissions including `READ_CONTACTS`, `ACCESS_FINE_LOCATION`, `READ_CALL_LOG`, `READ_SMS`, and background battery optimization exemptions.
* **Target Package Namespace in Jadx:**
  * `com.myled.HiwearPlus.*` (UI activities, branding layer).
  * `com.lianhezhuli.bt.*` or `com.lianhezhuli.hyfit.*` (Underlying United Power Bluetooth management service).
  * `com.myled.protocol.*` or `com.zhuli.protocol.*` (Command serializer and parser).

### 3.2 Static Decompilation Command
```bash
# Decompile base APK without resource decoding hang
jadx -d analysis/decompiled/hiwear \
     --show-bad-code \
     --no-res \
     analysis/apk/com.myled.HiwearPlus.apk
```

### 3.3 Key Inspection Targets in Code
* Search for GATT UUID constants: `6E400001`, `0000FF00`, `0000180F`.
* Search for the packet magic byte: `0xDF` (decimal `223` or hex `0xDF`).
* Search for dial packing classes: `DialManager`, `CustomDialActivity`, `WatchFaceUtils`.

---

## 4. BLE GATT Profile & Communication Channels

The watch advertises either as `C900`, `C900 Ultra`, `Watch-Call`, or `Hiwear-*`. Once connected, it exposes four primary GATT services `[W]`:

```
+---------------------------------------------------------------------------------+
|                       C900 GATT Service Architecture                            |
+---------------------------------------------------------------------------------+
|                                                                                 |
| 1. Nordic UART Service (NUS) [Primary Data Channel]                             |
|    UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9F                                   |
|    - Write (Without Response): 6E400002-B5A3-F393-E0A9-E50E24DCCA9F             |
|    - Notify:                   6E400003-B5A3-F393-E0A9-E50E24DCCA9F             |
|                                                                                 |
| 2. Vendor Command Service [Command & Configuration]                             |
|    UUID: 0000FF00-0000-1000-8000-00805F9B34FB                                   |
|    - Write / Write-No-Resp:    0000FF02-0000-1000-8000-00805F9B34FB             |
|    - Notify:                   0000FF01-0000-1000-8000-00805F9B34FB             |
|                                                                                 |
| 3. Standard SIG Battery Service                                                 |
|    UUID: 0000180F-0000-1000-8000-00805F9B34FB                                   |
|    - Read / Notify:            00002A19-0000-1000-8000-00805F9B34FB             |
|                                                                                 |
| 4. Device Information Service (DIS)                                             |
|    UUID: 0000180A-0000-1000-8000-00805F9B34FB                                   |
|    - Hardware / Firmware Rev:  00002A26 / 00002A27                              |
+---------------------------------------------------------------------------------+
```

* **No Bonding Required:** Connections are accepted without OS-level Bluetooth pairing.
* **Negotiated ATT MTU:** Android client requests MTU 512; Linux `bleak` defaults to 23 or 247. The packet slicer must dynamically scale based on actual negotiated MTU.

---

## 5. Wire Protocol & Packet Framing (United Power / HryFine Standard)

All data synchronization and settings flow across the Nordic UART Service (`6E400002` write, `6E400003` notify).

### 5.1 App-to-Watch Request Frame Layout
Frames transmitted from the host client to the watch use a 10-byte header with a trailing payload:

$$\text{Frame} = [\mathtt{0xDF}] \,|\, [\text{Len}_{\text{hi}}] \,|\, [\text{Len}_{\text{lo}}] \,|\, [\text{Checksum}] \,|\, [\text{Cmd}] \,|\, [\mathtt{0x01}] \,|\, [\text{Sub}] \,|\, [\text{PayLen}_{\text{hi}}] \,|\, [\text{PayLen}_{\text{lo}}] \,|\, [\text{Payload}]$$

| Offset | Size (Bytes) | Field Name | Description |
| :--- | :--- | :--- | :--- |
| **0** | 1 | `Header` | Fixed magic byte: `0xDF` (223 decimal). |
| **1..2** | 2 | `Total Length` | Big-endian 16-bit integer: length of frame excluding the first 4 bytes. $(\text{Len}_{\text{hi}} \ll 8) \mid \text{Len}_{\text{lo}}$. |
| **3** | 1 | `Checksum` | Modulo-256 additive checksum of all bytes in the frame, calculated with `byte[3] = 0x00`. |
| **4** | 1 | `Command` | Primary operational opcode (e.g., `0x02` for System/Time, `0xF3` for Device Info). |
| **5** | 1 | `Version` | Fixed protocol version tag: `0x01`. |
| **6** | 1 | `Sub-Command`| Sub-operation selector under the primary command opcode. |
| **7..8** | 2 | `Payload Len` | Big-endian 16-bit integer: length of following `Payload` data. |
| **9..end**| $N$ | `Payload` | Parameter bytes specific to the command. |

#### Checksum Calculation Algorithm
```python
def compute_df_checksum(frame: bytearray) -> int:
    """Calculates modulo-256 checksum over the frame with byte 3 cleared."""
    temp = bytearray(frame)
    temp[3] = 0x00
    return sum(temp) & 0xFF
```

### 5.2 Watch-to-App Acknowledgement Frame Layout
When the watch receives a command, it returns an acknowledgment on `6E400003`:

$$\text{ACK Frame} = [\mathtt{0xFD}] \,|\, [\mathtt{0x00}] \,|\, [\mathtt{0x05}] \,|\, [\text{Checksum}] \,|\, [\text{Cmd}] \,|\, [\text{Key}] \,|\, [\text{AckLen}_{\text{hi}}] \,|\, [\text{AckLen}_{\text{lo}}] \,|\, [\mathtt{0x01}]$$

* **Magic Byte:** `0xFD` (indicates incoming response/ack).
* **Length:** Fixed 5-byte payload indicator (`0x00 0x05`).
* **Key:** Command sequence or echo identifier.
* **Status Byte:** Last byte `0x01` indicates execution success; `0x00` indicates refusal/error.

### 5.3 Core Opcode Dispatch Table

| Command (`Cmd`) | Sub-Cmd (`Sub`) | Purpose | Payload Structure |
| :--- | :--- | :--- | :--- |
| **`0xF3`** | `0x00` | Query Device Info | Empty payload (`PayLen = 0x0000`). Replies with hardware ID, screen size, firmware string. |
| **`0x02`** | `0x0A` | Synchronize Time | `0x01` followed by 6 bytes: `[YY, MM, DD, HH, MM, SS]` (binary or BCD). |
| **`0x02`** | `0x01` | Set 12h/24h Format | 1 byte: `0x00` = 24-hour, `0x01` = 12-hour. |
| **`0x07`** | `0x01` | Find Device (Vibrate) | 1 byte: Duration counter (e.g., `0x05` for 5 vibrations). |
| **`0x05`** | `0x01` | Remote Camera Shutter | 1 byte: `0x01` enters camera mode, `0x02` exits. Watch button returns shutter trigger. |
| **`0x04`** | `0x01` | Watch Face Prep | Dial size (4 bytes u32), target flash address block, dial index. |
| **`0x04`** | `0x02` | Watch Face Chunk | Data chunk offset (4 bytes u32) + raw binary chunk (MTU sized). |

---

## 6. Watch Face (Dial) Binary Format & Transfer Mechanics

Unlike the Beambox (which receives raw JPEG images wrapped in an IMB or `0x12345678` container), the C900 uses compiled binary dial files (`.bin`).

### 6.1 Binary Dial Layout
```
+-----------------------------------------------------------------+
| Offset  0x00: Magic Identifier (e.g., "ZL\x01\x00" or "AB_DIAL")|
+-----------------------------------------------------------------+
| Offset  0x08: Target Screen Dimensions (u16 Width, u16 Height)  |
+-----------------------------------------------------------------+
| Offset  0x0C: Color Depth & Format Flag (0x10 = RGB565 raw)     |
+-----------------------------------------------------------------+
| Offset  0x10: Thumbnail Offset & Size (128x128 preview bitmap)  |
+-----------------------------------------------------------------+
| Offset  0x20: Widget Coordinate Table                           |
|               - Time X/Y, Date X/Y, Step Counter X/Y            |
+-----------------------------------------------------------------+
| Offset  0x60: Numeric Digit Glyph Tables (Bitmaps for 0-9)      |
+-----------------------------------------------------------------+
| Offset 0x100+: Full Screen Background Bitmap (Raw RGB565 LE)    |
+-----------------------------------------------------------------+
```

### 6.2 Encoding Color Data (RGB565)
The display controller consumes 16-bit little-endian **RGB565**:
$$\text{RGB565} = ((R \gg 3) \ll 11) \mid ((G \gg 2) \ll 5) \mid (B \gg 3)$$
```python
def pixel_to_rgb565_le(r: int, g: int, b: int) -> bytes:
    val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return val.to_bytes(2, byteorder="little")
```

---

## 7. Critical Hazards: The OTA Bootloader Deathtrap

<Callout type="danger">
DO NOT TOUCH SERVICE 0x18A8 (Cus5610) OR ATTEMPT BLE OTA UPGRADES.
</Callout>

### 7.1 Field Findings from Community Bricks
Reverse-engineering efforts documented on r/hardwarehacking (attempting custom firmware over BLE) permanently bricked multiple watches via these mechanisms:
1. **Instruction Set Confusion:** The bootloader accepts bytes without validating CPU architecture. Writing ARM or Telink (TC32) machine code to the Bluetrum RISC-V flash causes the CPU to lock permanently upon reboot.
2. **Bootloader Region Overwrite:** The running OTA bootloader sits between offset `0x00000` and `0x01FFFF`. Overwriting this sector wipes the running bootloader mid-stream, dropping Bluetooth permanently.
3. **Client Rule for `reWatch`:** Restrict all operations to runtime application characteristics (`6E400002`). Blacklist Service `0x18A8` and `0x18A0` in the client transport.

### 7.2 Hardware Recovery (Bench Reality)
If the watch is corrupted, it cannot be revived over the air. Physical unbricking requires:
* Opening the rear plate (desoldering the battery).
* Locating the Bluetrum download test pad: **Pin PB3** (often multiplexed onto the internal USB $D+$ test pad; sometimes PA7).
* Connecting a 3.3V USB-UART with TX and RX tied together through a $200\,\Omega$ resistor (single-wire half-duplex) using `github.com/kagaimiq/bluetrum-tools` (`download.py`).

---

## 8. `reWatch` Python Client Architecture

The clean-room client structure mirrors `reBeamBox`:

```
reWatch/
├── rewatch/
│   ├── __init__.py
│   ├── cli.py             # CLI commands: scan, probe, set-time, send-dial
│   ├── link.py            # BleakLink abstraction & RecordingLink (dry runs)
│   ├── protocol.py        # 0xDF/0xFD frame builders, parsers, and checksums
│   ├── media.py           # Image resize (320x385 / 240x286), RGB565 converter
│   ├── dial.py            # Dial .bin package assembler
│   ├── session.py         # Async state machine, MTU chunking, ACK timeouts
│   └── sim.py             # Software simulator mocking C900 responses
├── tests/
│   ├── test_protocol.py   # Modulo-256 checksums, frame round-tripping
│   ├── test_dial.py       # RGB565 packing, dial header serialization
│   └── test_no_vendor.py  # Zero outbound analytics verification
├── docs/
│   └── hiwear.md          # This technical reference
└── pyproject.toml
```

### 8.1 Pure Frame Builder Implementation (`rewatch/protocol.py`)
```python
def build_hiwear_frame(cmd: int, sub: int, payload: bytes = b"") -> bytes:
    """Builds a verified 0xDF request frame for Hiwear Plus / HryFine."""
    pay_len = len(payload)
    # Total length = header remainder (6 bytes: Cmd, Ver, Sub, PayLenHi, PayLenLo, Checksum) + payload
    total_len = 6 + pay_len
    
    frame = bytearray()
    frame.append(0xDF)                        # Magic
    frame.append((total_len >> 8) & 0xFF)     # Len Hi
    frame.append(total_len & 0xFF)            # Len Lo
    frame.append(0x00)                        # Checksum placeholder
    frame.append(cmd & 0xFF)                  # Command
    frame.append(0x01)                        # Version
    frame.append(sub & 0xFF)                  # Sub-command
    frame.append((pay_len >> 8) & 0xFF)       # Payload Len Hi
    frame.append(pay_len & 0xFF)              # Payload Len Lo
    frame.extend(payload)                     # Payload
    
    # Calculate checksum (sum mod 256 with byte 3 = 0)
    frame[3] = sum(frame) & 0xFF
    return bytes(frame)
```

---

## 9. Step-by-Step Reverse Engineering Execution Plan

<Steps>
  <Step subtitle="Static APK Audit" title="Decompile and Extract Opcodes">
    1. Download `com.myled.HiwearPlus` base APK.
    2. Decompile using Jadx into `analysis/decompiled/hiwear/`.
    3. Grep for `0xDF` and locate the primary command processor class to extract any secondary sub-commands not documented here.
  </Step>

  <Step subtitle="Live Android Capture" title="Record Bluetooth HCI Snoop Trace">
    1. Pair the C900 with an Android device running the official Hiwear Plus app.
    2. Enable "Bluetooth HCI snoop log" in Developer Options.
    3. Trigger: Time Sync, Find Device, and one custom Watch Face change.
    4. Pull `btsnoop_hci.log` via ADB and inspect with Wireshark filtering on `btatt.service == 6e400001-...`.
  </Step>

  <Step subtitle="Dry-Run Simulation" title="Build Mock Software Tests">
    1. Implement `build_hiwear_frame` and parser in `rewatch/protocol.py`.
    2. Write pytest test cases validating frames against known good traces from the HCI log.
    3. Ensure `sim.py` accurately echoes `0xFD` acknowledgments.
  </Step>

  <Step subtitle="First Hardware Contact" title="Pair and Sync Time via Python">
    1. Run `rewatch probe` to connect and print the GATT characteristic table.
    2. Execute `rewatch set-time` over BLE using `BleakLink`.
    3. Verify the watch face clock updates immediately on the physical LCD.
  </Step>
</Steps>