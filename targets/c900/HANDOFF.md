# Handoff: C900 watch

Updated: 2026-10-14 (Asia/Saigon). Status: Gate G4 completed (Android client built and unit-tested; never run on live device). Ready for owner-attended live session (Part B / LIVE-APP-1).

## 1. What is done
- **Core protocol library (`:core`)**: Pure Kotlin/JVM, 0 Android framework imports.
  - Framing codec (`Frames.kt`): `DF` data / `FD` ack, checksum calculation with byte 3 zeroed, strict blocklist of dangerous commands (0x01, 0x04, 0x06, 0x07, 0x0D, 0x13).
  - Reassembly & resync (`FrameReader.kt`): 9..1024 B framing, session flood caps, corrupt frame discard.
  - Command builders (`Commands.kt`): allowlisted commands only (time sync, find watch, message push, 12/24h format, feature query).
  - Paced command queue (`CommandQueue.kt`): single GATT write in flight, ATT piece chunking (20 B, 20 ms piece interval), 100 s hard timeout, 200-write session budget.
  - State machine (`Session.kt`): connect order, 0x2A27 hardware revision major decoding, feature gating, unsolicited 0x0E key 1 silent Classic MAC caching (owner decision 2026-10-14), 0x0C key 19 bond prompt.
  - Health record parsers (`HealthRecords.kt`): shared 2-byte date decoder, cmd 5 key decoders for key 2 (hourly steps), key 4 (heart rate), key 5 (blood pressure), key 9 (sleep summary), key 12 (day total with bounds clamp), key 13 (temperature with signed tenths), key 14 (SpO2), key 15 (sport sessions with 30 B records).
  - Health sync coordinator (`HealthSync.kt`): tracks cmd 5 start/end markers, collects records during sync, exposes immutable `SyncedHealthData` strictly when `DONE`, zero outbound writes.
- **Android app shell (`:app`)**: Plain Android Views, 0 external UI dependencies, 0 Room dependencies.
  - BLE transport (`GattLink.kt`): strict binding to command service (`6e400001-...`) write `0002` and notify `0003`, OTA service deny list, thread marshaling of all Bluetooth callbacks to main looper with stale instance guards.
  - Write scheduler (`PacingScheduler.kt`): single operation in flight with 20 ms piece delay and denied UUID drop.
  - Foreground service (`WatchService.kt`): owns `Session`, `CommandQueue`, `HealthSync`, `HealthStorage`, manages 10000 ms disconnect / 3000 ms connect fail reconnect loops.
  - Notification forwarding (`NotifyListener.kt`, `NotificationMapper.kt`): NotificationListenerService with 23 app types, unmapped apps disabled by default, ongoing/group/own package filtering, 2000 ms duplicate suppression (`NotificationDeduplicator.kt`).
  - Local storage (`HealthStorage.kt`, `HealthDeduplicator.kt`): plain SQLite (`health.db`) with composite primary keys `(date, time)` per record kind, `CONFLICT_REPLACE` upserts, pure deduplication unit tests.
  - User interface:
    - Device picker (`MainActivity.kt`): scans for "Watch Ultra" with `BLUETOOTH_SCAN (neverForLocation)`.
    - Settings (`SettingsActivity.kt`, `NotificationSettings.kt`): per-type notification switches backed by SharedPreferences.
    - Status (`StatusActivity.kt`): connection state, battery, ver, day totals, write budget, last 7 days of steps, distance (km), kcal from storage, manual Find (1 write) and Time (1 write) buttons.
- **Continuous Integration**:
  - Multi-platform Python test matrix (Linux, macOS, Windows) running 150 tests, repo lint, and strict privacy scan.
  - GitHub Actions job (`core-test`) running `:core:test` on ubuntu-latest with JDK 21 and Gradle 8.10.2.
- **Test suite**: 81 Kotlin unit tests (37 `:core` + 44 `:app`) and 150 Python tests pass with 0 failures.

## 2. Evidence summary: [C] vs [I] / [U]
- **Confirmed in artifact bytecode [C]**:
  - NUS command UUIDs (`6e400001-...`, write `0002`, notify `0003`).
  - Framing: `DF` data, `FD` ack, length = plen + 5, checksum with byte 3 zeroed.
  - Time year offset: -2000 (0x7D0).
  - Health date packing: `year = 2000 + ((b0 & 0x7F) >> 1)`, `month = ((b0 & 1) << 3) | (b1 >> 5)`, `day = b1 & 0x1F`.
  - Units: distance in meters, calorie in calories; UI formats with / 1000.0f as km and kcal.
  - Key 2 hourly steps: 24 x 8 B records, 0xFFFF = none, steps > 20000 clamped to 20000 steps, 20000 m, 400000 cal.
  - Key 4 HR: bpm kept if 40..160.
  - Key 5 BP: systolic kept if 50..300, diastolic kept if 30..200.
  - Key 9 sleep: light, deep or awake > 1439 resets all three to 0.
  - Key 12 day total: steps > 240000, distance > 192000 or calorie > 4464000 resets all three to 0.
  - Key 13 temp: degrees + (signed tenths / 10.0), kept if 30.0..50.0.
  - Key 15 sport: stride 30 B (start, end, duration, mode, hr, calorie, modeData1..3).
  - Notification app mappings: 23 known apps, other = 13, text cut at 196 B.
  - ATT piece chunking: 20 B pieces, 20 ms piece pacing.
  - Reconnect timers: 3000 ms on connect failure, 10000 ms on disconnect.
- **Confirmed on live hardware or HCI snoop [H]**:
  - BLE advertised name: `Watch Ultra`, company ID 0x314C, manufacturer data holds watch MAC + `12 34`.
  - Watch accepts `find` (cmd 2 key 11), `time` (cmd 2 key 1), and `message` (cmd 2 key 18) without prior bind (cmd 3 key 0) while bound to companion phone.
  - 0x2A27 reads `"10000"` -> app version byte `0x10` (`10000 & 0xFF`).
  - Watch ack line: `FD 00 05 <sum> <cmd> <key> <len_hi> <len_lo> <status>` where `status=1` and length = total acked frame length.
  - Unsolicited inbound `cmd 0x0E key 1` emitted by watch after message transmission.
  - Transport operates without LE SMP or encryption.
- **Inferred [I] (placeholders with revisit criteria)**:
  - `HealthSync.IDLE_TIMEOUT_MS = 30000L`: placeholder idle timeout to reset stalled sync (revisit if full-sync capture shows gaps near or above 30 s).
  - `NotificationDeduplicator.WINDOW_MS = 2000L`: placeholder duplicate message suppression window (revisit if owner reports rapid intentional duplicate alerts).
  - `TEMPERATURE_CELSIUS = true`: degrees Celsius inferred from 30.0..50.0 bounds.
  - `SPORT_DURATION_SECONDS = true`: duration unit inferred from seconds of day start/end delta.
- **Unknown [U] (requires hardware capture or physical inspection to settle)**:
  - Meaning of `modeData1..3` per sport mode in cmd 5 key 15.
  - Meaning of `rawType` byte in heart rate (key 4) and temperature (key 13).
  - Whether SpO2 (key 14) can push multi-record payloads in history sync.
  - Real watch flash wear cost per write and total notification store capacity.
  - Real behavior of unbound watch upon first LE connection (Q03).

## 3. What only hardware can settle
| Unknown | Test | Pass / fail criterion |
|---|---|---|
| Real BLE connection and MTU negotiation | LIVE-APP-1 step 1 | Service discovery succeeds; 4 device info reads complete; state reaches READY |
| Real watch display rendering of notifications | LIVE-APP-1 step 6 | SMS notification text appears legibly on watch display without truncation artifacts |
| Real watch physical reaction to Find / Time | LIVE-APP-1 steps 4-5 | Watch vibrates and displays "found" message; watch clock synchronizes with phone time |
| Inbound 0x0E key 1 Android handling | LIVE-APP-1 step 6 | Watch broadcasts Classic MAC; app silently caches address without Android OS pairing popup |
| Real history sync throughput | HW full sync capture | Cmd 5 records transmitted across keys 2, 4, 5, 9, 12, 13, 14, 15 without ATT piece drop |

## 4. Exact next command (Part B: Live Run)
Part B requires the owner present holding the watch. Do NOT run unattended.

When the owner is present and instructs "go":
1. Open the run sheet:
   ```bash
   cat targets/c900/tasks/LIVE-APP-1.md
   ```
2. Verify pre-flight checklist on phone and watch:
   - Phone Bluetooth enabled, watch in range and powered on.
   - Install APK via adb:
     ```bash
     adb install -r client/c900-android/app/build/outputs/apk/debug/app-debug.apk
     ```
   - Grant runtime Nearby Devices permissions and Notification Access.
   - In Settings screen, verify "Push other unmapped apps" is OFF and only SMS is enabled.
3. Launch `MainActivity`, tap "Watch Ultra", and execute the 6 steps of `LIVE-APP-1.md` strictly within the 3-write budget (1 Find, 1 Time, 1 SMS).
4. Record observations in `targets/c900/tasks/results/LIVE-APP-1-<date>.md`.
