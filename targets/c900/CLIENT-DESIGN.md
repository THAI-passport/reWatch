# C900 open companion: client architecture (DRAFT, design only)

**STATUS: DRAFT, pending owner sign-off.** Written 2026-10-13 in DEEP-PASS-1. Design only: no implementation is approved. Phase 3 (client) and Phase 4 (OTA, faces, contacts) stay deferred per PLAN.md; NEXT-STEPS section 6 lists what must be true before Phase 3 starts. Facts are cited by section; values live in PROTOCOL.md, FACTS.md and INVARIANTS.md and are not restated here.

## 1. Goal and non-goals
Goal: an ad-free, open-source, local-only companion for the C900 that does what an owner uses daily: keep time, push phone notifications, find the watch, show battery, and pull health records into local storage, with settings the watch exposes.

Non-goals (never, or Phase 4 with a reviewed design): firmware OTA, watch-face upload, DIY backgrounds, contacts push (all ride the OTA channel, INVARIANTS I-40); unbind, reset, factory commands (I-20); any vendor server call (PROTOCOL section 8: inventory only); accounts, cloud sync, analytics, ads.

## 2. Platform options
| Option | Pros | Cons | Fit |
|---|---|---|---|
| **Android, Kotlin (Jetpack Compose)** | Full BLE control (MTU, write type, bond state visible and controllable); `NotificationListenerService` for notification forwarding; `CompanionDeviceManager` for background reconnects; foreground service for sync; the vendor app is Android, so behaviour and timings match | Android only; Kotlin needs a port of the codec (small: frames.py is about 100 lines) | Best for a daily companion |
| Flutter (`flutter_blue_plus` or similar) | One UI code base for Android and iOS | Notification forwarding still needs native Android code; plugin hides bond and write-type details we must control (I-30, write without response); iOS side cannot read other apps' notifications at all, so its value is limited to time/find/battery/health | Second choice if iOS is a must |
| Web Bluetooth PWA | No install; easy to audit | Chrome-only (no Safari/iOS); no background, no reconnect, no notification forwarding; the page must stay open | Good as a read-only diagnostic page, not a companion |
| Desktop (Python + bleak) | Reuses `client/c900/frames.py` and the probe's safety code directly; best for development, simulator, capture replay | Not with the user all day; no phone notifications | Keep as the reference implementation and test harness |

**Recommendation:** Android native Kotlin for the companion, with a pure-Kotlin protocol core (no Android imports) that is tested against byte vectors exported from the Python reference (`frames.py`, `c900_decode.py`). Keep the Python side as the reference codec, simulator and capture decoder. Revisit Flutter only if the owner needs iOS, and then only after checking whether the C900 supports ANCS [U], since iOS apps cannot forward notifications themselves.

## 3. Layers
```
UI (Compose, Lucide icons)            screens: device, notifications, health, settings, diagnostics
  |
App services                          sync scheduler, notification bridge, export
  |
Session / bind state machine          connect order, bind, feature gating, bond policy
  |
Command queue                         one in flight, ack match, timeout, NAK handling
  |
Framing codec (pure)                  DF/FD build/parse, checksum, reassembly, payload codecs
  |
Transport                             GATT: command service only, write w/o response, 20-byte pieces
```
Each layer depends only on the one below through an interface, so the simulator and the capture replayer plug in under the codec.

### 3.1 Transport
- Binds to characteristic objects of the command service `...DCCA9F` (write `0002`, notify `0003`) found by walking that service, never by UUID lookup across the whole GATT table (the probe's DEEP-PASS-1 fix). Battery 0x180F and Device Information 0x180A are read-only.
- OTA isolation: the transport module has no API that accepts a service or characteristic chosen by a caller. The OTA services (0xFF00, 0x18A8, `...DCCA9E`, PROTOCOL section 2) are on a deny list checked at discovery; the module refuses to subscribe, read or write them. OTA code, if ever written (Phase 4), lives in a separate module and build flavour that the default app does not include.
- Write without response, 20-byte pieces, 20 ms apart; retry rules from I-16; a failed write disconnects (PROTOCOL section 3). MTU: the app requests 32 normally [C]; the client requests the same so piece behaviour matches.
- Reassembly with resync and caps (frame 9..1024 bytes; per-session flood cap), as in the probe's `FrameReader`.

### 3.2 Framing codec
- Same semantics as `client/c900/frames.py`: header, length (payload + 5), checksum (sum with byte 3 as zero), ack layout, `BLOCKED_CMDS`. The `ver` byte is an input taken from the 0x2A27 major (I-10), not a constant.
- Builders exist only for allowlisted (cmd, key) pairs; there is no generic `build(cmd, key, bytes)` in the app build. Adding a pair needs a test, a FACTS citation, and a write-cost note.
- Payload codecs: time (I-21), message (PROTOCOL section 5), find, 12/24 h (I-22), health date (I-36) and records (PROTOCOL section 7.2). Private payloads (message text, caller, profile, location) are never logged (same list as `tools/c900_decode.py` PRIVATE).
- Shared test vectors: a JSON file generated by the Python reference and checked by both test suites.

### 3.3 Command queue
- One command in flight; the next waits for the ack (I-15). Match ack by cmd and key; status 1 = ok; NAK or unknown ack = error surfaced to the caller, never silently retried.
- Timeout: the app waits 100 s then disconnects (I-15). The client keeps 100 s as the hard limit but shows "waiting" in the UI after a few seconds.
- No automatic resend of a whole frame on timeout; the caller decides. Settings writes are debounced (one write per setting per change, at most a few per minute) until the write cost is known (ground rule 7).
- The client answers inbound DF frames with the app's ACK (`x = 0, status 1`) and bad-sum frames with the NAK (`x = 3, status 0`), as PROTOCOL section 4 says the app does.

### 3.4 Session and bind state machine
States: `Idle -> Connecting -> Discovering -> ReadingInfo (0x2A27, 0x2A26, features, battery) -> Binding -> Ready -> Syncing -> Ready`, plus `Error` and `Disconnected`. Connect order follows I-35.
- Feature map gates every feature (byte 0 must be 0xAA, I-32); unknown bits disable the feature rather than guess.
- Bind (cmd 3 key 0 with a per-install 8-character id, PROTOCOL section 3): the watch answers 0x0C key 8 (accept) or 9 (refuse) [C]. Binding a new id may displace the vendor app's binding [I], so the first bind is an explicit user action with a warning, never automatic. The vendor server bind call is not made.
- Bond policy: the client never calls `createBond` on its own. The three app triggers (I-30) become a user prompt ("The watch asks to pair. Allow?") with "No" as the default; declining is logged and the session continues if the watch allows it.

### 3.5 Health sync and local storage
- Pull records with cmd 5 keys (PROTOCOL section 7.2); parse with the I-36 date packing; store in a local SQLite/Room database keyed by record date and type; idempotent upsert so re-sync never duplicates.
- Units for distance and calorie are [U]: store raw values plus a `unit_unknown` flag; show raw until a capture or the watch screen settles them.
- Export: optional, user-started, to a local CSV or JSON file (and, if wanted later, Android Health Connect). No upload.

### 3.6 Notification push
- `NotificationListenerService` with a per-app allowlist chosen by the user (default: nothing forwarded). Message push uses cmd 2 key 18, type table from C900-Q04, text cut at 196 bytes (PROTOCOL section 5).
- Rate limit (for example one push per few seconds, coalesce bursts) until write cost and the watch's message store size are known.
- Calls (cmd 2 key 17) only if the feature map allows and the user opts in; the caller name is private data and never logged.

### 3.7 Settings
Only settings with [C] layouts and an explicit user action: time format (I-22), units, raise-to-wake, DND window, find watch. Each setting write is one command, debounced, with the ack shown. Alarms, weather and sedentary reminders come later (payloads in C900-Q04).

## 4. Safety carried over from the probe
| Probe rule | Client rule |
|---|---|
| Allowlist of (cmd, key), `BLOCKED_CMDS` refused | Same, in the codec; the blocklist test is shared |
| OTA UUID deny list, writes bound to command-service objects | Same, in the transport; no caller-chosen characteristics |
| Never calls pair; aborts on bond triggers | Never bonds without a user "Allow"; triggers become prompts |
| Write caps, connection caps, global timeout | Per-session write budget for settings and pushes; reconnect backoff with a cap; disconnect loop detection |
| Version byte must match the app's | `ver` from 0x2A27; refuse to send if unreadable |
| Untrusted device strings sanitized | Same; device names and DI strings are display-only, never format strings or paths |
| Logs masked, private payloads redacted | Diagnostics log off by default; when on, masks addresses and never stores message text, caller, profile, location |

## 5. Privacy
- No vendor server, no account, no analytics, no ads, no network permission in the default build.
- All data stays on the phone; export only on user action, to a file the user picks.
- Diagnostics export uses the same masking as the probe and the decoder.

## 6. UI
No emoji anywhere; icons from Lucide only (an icon pack port for Compose, or vector drawables generated from Lucide SVGs, with its licence file shipped). No ads, no upsell screens. Screens: Device (connection, battery, firmware, feature list), Notifications (per-app allowlist, test push), Health (day view, history, export), Settings (watch settings with ack status), Diagnostics (masked log, frame counts, "safe mode" that disables all writes).

## 7. Test strategy
- Codec unit tests from shared vectors (Python reference and Kotlin), including every worked example in PROTOCOL section 9.
- Simulated watch (the Python `SimWatch` grown into a scripted peer, or a Kotlin twin) under the transport interface: bind accept/refuse, acks, NAKs, bond-trigger frames, floods, disconnects. A simulator proves consistency only (ground rule 6); nothing becomes [H] from it.
- Capture replay, decode-only: feed an owner capture through the reassembler and parsers and compare with `tools/c900_decode.py` output. Replay never sends anything to a device.
- Safety tests mirrored from `tests/test_c900_probe.py`: no write path to OTA UUIDs, blocked commands unbuildable, no bond without consent, caps enforced.
- Hardware acceptance only through approved live sessions (`tasks/LIVE-SESSION-1.md` and its session 2).

## 8. Feature map: evidence and phase
Evidence columns: **[C] only** = layout read from the app, not seen on a wire; **capture** = an owner HCI capture would settle it; **hardware** = needs our own approved live session.

| Feature | Evidence now | Settled by | Phase | Blocked by |
|---|---|---|---|---|
| Connect, discover, read DI/battery/features | [C] | session 1 or capture | 3a | Q02, version, features [U] |
| Version byte from 0x2A27 | [C] rule | session 1 or capture | 3a | C900 value [U] |
| Bind (cmd 3 key 0) and accept/refuse | [C] | capture (preferred) | 3b | effect on existing phone binding [U]; ack bytes [U] |
| Time sync | [C] smali | capture or session 2 | 3b | watch ack [U]; I-30 bond on ack if b15 set |
| Find watch | [C] | capture or session 2 | 3b | watch ack [U] |
| Battery (0x2A19 read/notify) | [C] | session 1 or capture | 3a | none beyond services |
| Message push | [C] | capture or session 2 | 3c | type table per feature bits; store size and write cost [U] |
| Call notification (cmd 2 key 17) | [C] | capture | 3c | private payload rules; feature bit |
| Find phone (inbound 0x0C keys 1/15) | [C] | capture or session 1 (if the user taps it) | 3c | none |
| Camera shutter (inbound 0x0C key 2) | [C] | capture | 3d | low priority |
| Health sync (cmd 5) | [C] field maps | capture | 3d | distance/calorie units [U]; history start/end handshake on the wire |
| Settings: 12/24 h, units, raise-to-wake, DND | [C] | capture | 3d | write cost [U] |
| Alarms, weather, sedentary | [C] (C900-Q04) | capture | 3e | write cost [U] |
| Bond handling (prompts) | [C] app side | capture shows whether the C900 asks | 3b | Q03 [U] |
| Contacts, faces, wallpapers, firmware | [C] OTA path | not planned | 4 or never | ground rule 7, I-40 |

## 9. Open questions that block each layer
| Layer | Blocking unknowns | Where tracked |
|---|---|---|
| Transport | Services actually exposed (Q02); MTU the watch accepts | OPEN-QUESTIONS Q02 |
| Codec | `ver` value; watch ack bytes 6-7 (I-18) | FACTS section 4 |
| Command queue | Which keys the C900 acks; NAK behaviour on the watch side | NEXT-STEPS section 6 |
| Session/bind | Bind effect on the vendor app; whether the watch asks to bond (Q03) | OPEN-QUESTIONS Q03 |
| Health | Units; real record counts; history handshake timing | C900-Q16, capture |
| Notifications | Message store size; flash wear per message | ground rule 7, capture |
| UI | none blocking | - |

## 10. Owner decisions needed before Phase 3
1. Platform: Android Kotlin (recommended) or Flutter.
2. Whether the client may bind as its own "phone" (displacing the vendor app) or must coexist.
3. Default bond answer when the watch asks: "No" (recommended).
4. Phase 3 scope (suggested 3a + 3b first: connect, info, battery, bind, time, find).
