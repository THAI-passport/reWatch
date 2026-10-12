---
name: re-watch-targets
description: What is specific to smartwatches and bands when reverse engineering their companion apps - common vendor stacks (Jieli, Realtek, Nordic and DFU, Telink, Huami/Zepp), standard GATT services (battery, heart rate, current time, alert notification, ANCS and AMS on iOS), typical features, how watch face and OTA formats are usually structured, which probes are read-only safe, and what to record per model family. Load at gate G0 and G2 for any watch or band.
---

# re-watch-targets

Everything here is background knowledge, not evidence about your target. Claims are tagged [W] (widely documented elsewhere, not verified by us for your device) or [U] (unknown or varies). Verify every item from the app you are analysing and re-tag it [C] or [I] in the target's FACTS.md and PROTOCOL.md.

## First questions for any watch
1. One app per model, or one app for a family? Many vendors ship a white-label app under several brands; the model list is often a server catalog. Record the mapping in FACTS.md.
2. Which chip family? It decides the transport and OTA. Evidence order: natives and SDK package names in the app, then FCC photos and teardowns [W].
3. Is there a standard-GATT layer, a vendor GATT layer, or both? Most watches have both.
4. Does the watch use classic Bluetooth (audio, calls) as well as BLE? The app side usually shows it with `BluetoothHeadset`, A2DP or SPP code [U].
5. Does the iOS app differ from the Android app (ANCS)? Notifications on iOS usually do not go through the app at all [W].

## Common stacks (recognition hints, [W])
| Stack | How it shows up in an app |
|---|---|
| Jieli (JL) | `libjl_*` natives, `com.jieli.*` packages, service 0xAE00; see `re-jieli` |
| Nordic nRF | Nordic DFU library (`no.nordicsemi.android.dfu`), DFU service 0xFE59 (secure) or the legacy 128-bit DFU service, Nordic UART service 6E400001-B5A9-F393-E0A9-E50E24DCCA9E |
| Realtek | `com.realsil` or `com.realtek` packages, a Realtek OTA library; service ids vary [U] |
| Telink | `com.telink` packages, a Telink OTA service with a 128-bit base [U] |
| Huami / Zepp | 16-bit services 0xFEE0 and 0xFEE1, an auth step using AES with a per-device key obtained at pairing; protocol details vary by generation [U] |
| Others (Actions, Bestechnic, Goodix, Dialog) | package names in the app and SDK docs; treat as unknown until read [U] |

## Standard GATT services worth probing first (read-only safe, [W])
| Service | UUID | Typical use |
|---|---|---|
| Generic Access | 0x1800 | device name, appearance |
| Device Information | 0x180A | manufacturer, model, firmware and hardware revision strings |
| Battery | 0x180F (level 0x2A19) | battery percent |
| Heart Rate | 0x180D (measurement 0x2A37) | notify only after subscribing; subscribing writes a descriptor |
| Current Time | 0x1805 (current time 0x2A2B) | read or write time |
| Immediate Alert / Find Me | 0x1802 | write alert level to ring the watch (a write, but one byte) |
| Alert Notification | 0x1811 | new alert and control point |
| Phone Alert Status | 0x180E | ringer state |
| Apple Notification Center (ANCS) | 7905F431-B5CE-4E99-A40F-4B1E122D00D0 | the watch pulls iOS notifications as a client |
| Apple Media Service (AMS) | 89D3502B-0F36-433A-8EF4-C502AD55F8DC | music control from iOS |
Reads of Device Information, Battery and Generic Access are the safest first contact. Subscribing to notifications writes a CCCD descriptor; that is a write and goes in the write budget, even though it is tiny.

## Typical features and where to look in the app
| Feature | What to find |
|---|---|
| Notifications | `NotificationListenerService` (Android) feeding a vendor frame with app id, title, text; limits on length and encoding (UTF-8, UTF-16, GBK) [U] |
| Watch face (dial) push | a list of dials from a server or bundled assets, a converter to the watch's resource format, then a file or OTA-like transfer. Record the pixel size, color format, compression, max file size and slot count |
| Music control | media session code mapping play, pause, next to vendor commands or AMS |
| Health sync | history pull: command per data type (steps, sleep, heart rate, SpO2), timestamps and unit conventions, ACK or cursor to continue |
| Find my watch | immediate alert or a vendor command; some apps also show a last-seen map from phone location only |
| Camera shutter | watch to phone key event; the phone app receives a notification or command and triggers capture |
| Time, language, units | usually the first writes after connect; low risk, but count them |
| Binding / pairing | a token or key exchange; look for AES, a stored key, an account id (never use the user's account) |

## Watch face and OTA formats (general shape, [U] for any given vendor)
- Watch face: a container with a header (magic, version, sizes, a table of resources), images in RGB565 or ARGB (sometimes paletted or LZ/RLE compressed), fonts, widget descriptors, and a checksum or signature. Many vendors accept only faces built by their tool for a specific screen size. Find the builder in the app or its server tool and record the byte layout with a worked example; do not copy vendor assets.
- OTA: a firmware image with a header and signature, sent in chunks with offsets, CRC and ACKs, followed by a reboot. Vendors differ widely. OTA is studied, never exercised, in this repo: an image that fails verification or is wrong for the board can brick the watch.
- Both usually reuse the vendor's file-transfer layer: study it once.

## Read-only safe versus not
| Class | Examples | Rule |
|---|---|---|
| Static | app, natives, docs, existing captures | always allowed |
| Passive BLE | scan, read standard characteristics, subscribe to notifications | needs the owner's approval for the session; subscriptions count as writes |
| Small writes | time sync, find-me, notification test | budgeted, one at a time, owner approval |
| Storage writes | watch face, wallpaper, contacts | budget with a daily cap, delta skipping, minimum interval; see `re-client-sim` |
| Never | OTA, format, delete all, factory reset, bootloader or debug pads | not without explicit owner approval for that exact action, and not as a protection bypass |

## Record per model family (FACTS.md table)
App name and package, app version and hash; model names and marketing names; chip and flash [W/C]; screen size, shape, resolution and framebuffer size; transports and selector; advertised names per mode; services seen; MTU observed; watch face format and limits; OTA stack (name only); notification fields; health data types; auth type; what was verified on hardware and by whom. Conflicting values go only in FACTS.md with a source for each.
