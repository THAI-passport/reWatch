# C900 open companion: Android (Kotlin)

Open-source, local-only Android companion app for the C900 smartwatch (`Watch Ultra`).
Design: `targets/c900/CLIENT-DESIGN.md`. Protocol: `targets/c900/PROTOCOL.md`.

## Modules
| Module | State | What |
|---|---|---|
| `core` | built and tested (pure Kotlin/JVM, no Android imports) | `Frames` codec, `FrameReader` reassembly/flood caps, `Gatt` UUID definitions/deny list, `Commands` frame builders (time, find, message, 12/24h, feature query), `CommandQueue` (one-in-flight, ack match, 100 s timeout, 200-write budget), `Session` state machine, `HealthRecords` (cmd 5 decoders for keys 2, 4, 5, 9, 12, 13, 14, 15 and shared 2-byte date decoder), `HealthSync` coordinator (exposes records when DONE). |
| `app` | built and tested (plain Android Views, SQLite, no Room, no external UI deps) | `GattLink` (GATT transport on NUS `...DCCA9F`), `PacingScheduler` (20 ms ATT piece pacing), `WatchService` (foreground service with 3 s / 10 s reconnect backoff), `NotifyListener` (NotificationListenerService forwarding with 23 app types, unmapped apps disabled by default, ongoing/group/own filter, 2 s dedupe), `HealthStorage` (plain SQLite `health.db` with composite primary keys), `HealthDeduplicator`, `MainActivity` (BLE scan for "Watch Ultra"), `SettingsActivity` (per-type notification switches), `StatusActivity` (connection, battery, ver, day totals, write budget, last 7 days history from storage, Find and Time buttons). |

## Build and Test
Requires JDK 21 and Gradle 8.10.2:

```bash
cd client/c900-android
gradle :core:test :app:testDebugUnitTest :app:assembleDebug
```

- `:core:test` runs 37 pure Kotlin JVM tests (including codec round-trips, fuzz tests, health record decoders).
- `:app:testDebugUnitTest` runs 44 JVM unit tests (PacingScheduler, ReconnectController, NotificationMapper, NotificationFilter, NotificationSettings, StatusSnapshot, HealthDedupe, EndToEndTest against simulated watch).
- `:app:assembleDebug` produces the debug APK at:
  `app/build/outputs/apk/debug/app-debug.apk`

## Install with ADB
Connect your Android phone via USB with USB debugging enabled:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

To view live service logs:
```bash
adb logcat -s reWatch WatchService
```

## Permissions to Grant
On Android 12+ (API 31+):
1. **Nearby Devices (Bluetooth)**:
   - When launching the app, grant `android.permission.BLUETOOTH_SCAN` and `android.permission.BLUETOOTH_CONNECT`.
   - Manifest explicitly sets `neverForLocation` on `BLUETOOTH_SCAN` (no location tracking).
2. **Notifications**:
   - Grant `android.permission.POST_NOTIFICATIONS` so the foreground service status and bond notifications can be displayed.
3. **Notification Access (for message forwarding)**:
   - To forward notifications to the watch, grant Notification Listener permission:
   - Go to phone **Settings -> Apps -> Special app access -> Notification access**.
   - Select **reWatch** and toggle **Allow notification access** to ON.

## Notification Controls: Turning Types On / Off
The app puts the user in complete control of notifications to prevent flash wear on the watch:
1. Open the app and tap **Settings** (`SettingsActivity`).
2. **Push other unmapped apps**:
   - Master switch for apps not in the known 23 categories.
   - Default: **OFF** (prevents high-frequency apps, download progress, music players from flooding the watch).
3. **Per-Category Switches**:
   - Toggle individual notification sources on or off:
     - SMS / Messaging
     - Phone Calls (rings only)
     - WhatsApp
     - WeChat
     - QQ
     - Skype
     - Twitter / X
     - Facebook / Messenger
     - Instagram
     - Line
     - KakaoTalk
     - Viber
     - Telegram
     - Gmail / Email
     - and others.
4. Settings are persisted locally in `SharedPreferences` and take effect immediately without restarting the service.

## Privacy & Safety Invariants
- Zero internet permission in `AndroidManifest.xml` (local-only companion; no analytics, no ads, no cloud sync).
- All health records remain on the phone in local SQLite storage (`health.db`).
- Notification text, caller names, and MAC addresses are never logged to logcat or disk.
- Session write budget: maximum 200 writes per session protects watch flash memory (Ground Rule 7).
