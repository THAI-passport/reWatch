# LIVE-APP-1: First Live Android App Run Sheet (Owner Present)

First live evaluation of the open companion Android application (`client/c900-android` `:app` module) against the physical C900 Watch Ultra hardware.

> [!IMPORTANT]
> **Owner approval required**: This sheet requires physical hardware and the owner present. An automated agent must **NEVER** execute these steps autonomously (ground rules 1, 2, 7).

---

## 1. Safety & Session Budget

| Parameter | Limit | Rationale |
|---|---|---|
| Connections | Exactly 1 GATT connection | Avoid connection churn and status 133 controller exhaustion |
| Info Reads | Exactly 4 reads | `0x2A27` (HW rev), `0x2A26` (SW rev), `0x2A28` (Features), `0x2A19` (Battery) |
| Feature Writes | At most 3 commands | 1 Find, 1 Time, 1 Message push (maximum 4 ATT pieces) |
| Total Write Budget | < 5 pieces (hard cap: 200) | Strict adherence to flash wear protection (ground rule 7) |
| Bonding | Zero pairing / bonding | No `createBond()` calls; 0x0E key 1 cached silently; 0x0C key 19 prompt default No |
| Retries | Zero manual retries | A timeout, disconnect, or NAK is a protocol result |

---

## 2. Pre-flight Environment Checklist

Complete every check before starting:
- [ ] Watch battery is charged to at least 50%.
- [ ] Vendor app (Hiwear Plus) is uninstalled or force-stopped with Bluetooth permissions revoked so it cannot compete for GATT.
- [ ] Host computer (Mac/PC) has disconnected Classic Bluetooth audio (`Watch Ultra`) in system settings.
- [ ] Android test device (Android 8.0+, API 26-35) has Bluetooth enabled.
- [ ] Build debug APK on host:
  ```bash
  cd client/c900-android && ~/tools/gradle/bin/gradle :app:assembleDebug
  ```
- [ ] Install debug APK onto test device via ADB:
  ```bash
  adb install -r app/build/outputs/apk/debug/app-debug.apk
  ```
- [ ] Grant Notification Listener access in Android Settings:
  `Settings -> Apps & notifications -> Special app access -> Notification access -> reWatch (toggle ON)`

---

## 3. Step-by-Step Execution Protocol

### Step 1: Launch and Grant Permissions
1. Open **reWatch** from the Android launcher (`MainActivity`).
2. Accept runtime permission dialogs for `BLUETOOTH_SCAN` and `BLUETOOTH_CONNECT` (Android 12+) and `POST_NOTIFICATIONS` (Android 13+).
3. Verify zero location permission requests appear (enforcing `neverForLocation`).

### Step 2: Device Scan
1. Tap **Start Scan**.
2. Verify scanner filters for advertised name `Watch Ultra` (FACTS section 1 [C]).
3. Verify scan progress bar animates and scan status updates.
4. Verify discovered item appears as `Watch Ultra #1` (MAC addresses and raw names are masked).
5. Tap **Stop Scan** (or allow 10 s timeout).

### Step 3: Connect and Observe Handshake
1. Tap the discovered device `Watch Ultra #1`.
2. The app automatically launches `StatusActivity` and starts `WatchService` foreground service.
3. Observe status screen fields transition:
   - **Connection State**: `Connecting...` -> `Discovering Services...` -> `Reading Device Info...` -> `Connected (Ready)`
   - **Battery**: Displays percentage (e.g. `85%`)
   - **Protocol Ver**: Displays `0x10`
   - **Writes (pieces)**: Displays `0 / 200`
4. Verify ongoing persistent notification `reWatch: C900 companion service running` appears in Android notification shade.

### Step 4: Write 1 — Find Watch Alert
1. Trigger Find command (1 piece, 10 bytes: cmd `0x02`, key `0x0B`, payload `0x01`).
2. Observe Watch:
   - Screen turns on with alert text ("the bracelet has been found!").
   - Motor vibrates.
3. Observe Status Screen:
   - Writes budget counter increments to `1 / 200`.

### Step 5: Write 2 — Time Synchronization
1. Trigger Time sync command (1 piece, 13 bytes: cmd `0x02`, key `0x01`, 4-byte packed time payload).
2. Observe Watch:
   - Watch clock face updates to match the Android phone's current local time.
3. Observe Status Screen:
   - Writes budget counter increments to `2 / 200`.

### Step 6: Write 3 — Message Push
1. Post a test SMS notification to the phone or send a test message from a supported app (e.g. SMS, Telegram).
2. Observe Watch:
   - Notification alert appears on watch display.
3. Observe Status Screen:
   - Writes budget counter increments by 1-2 pieces (total <= 4 / 200).

### Step 7: Observe Inbound Handling & Bond Triggers
1. Monitor watch unsolicited response following message push:
   - When watch emits `cmd 0x0E key 1`: verify `WatchService` silently caches MAC in memory, sends protocol ACK, and displays **zero** user prompt dialogs (owner decision 2026-10-14).
   - If watch emits `cmd 0x0C key 19`: verify `WatchService` posts a notification prompt with default No and never calls `createBond()`.

---

## 4. Abort Conditions & Immediate Stop Triggers

Stop the test immediately, disconnect GATT, and record the result if any of the following occur:
1. **OS Pairing Dialog**: Android displays a system Bluetooth pairing dialog ("Pair with Watch Ultra?"). Tap Cancel immediately, terminate the app, and record.
2. **Blocked Inbound Opcode**: Watch transmits blocked opcodes (`0x01`, `0x04`, `0x06`, `0x07`, `0x0D`, `0x13`).
3. **Firmware / DFU Screen**: Watch displays an unexpected bootloader, firmware flash, or upgrade progress icon.
4. **Write Budget Acceleration**: Session write counter exceeds 10 writes without explicit user actions.
5. **Rapid Reconnect Loop**: Service cycles reconnects faster than the 10 s disconnect / 3 s error backoff.

---

## 5. What to Record

Record findings in `targets/c900/tasks/results/LIVE-APP-1-<YYYYMMDD>.md`:
1. Phone model and Android OS version (`Build.VERSION.RELEASE`, API level).
2. Exact status screen values upon reaching `Connected (Ready)` (battery, version).
3. Physical watch responses for Find, Time, and Message.
4. Total writes count from `CommandQueue` at session end.
5. Filtered logcat output:
   ```bash
   adb logcat -d -s rewatch:* AndroidRuntime:* > live-app-1.log
   ```
6. Run privacy scan prior to saving notes:
   ```bash
   python3 tools/privacy_scan.py targets/c900/tasks/results/LIVE-APP-1-<YYYYMMDD>.md --strict
   ```
