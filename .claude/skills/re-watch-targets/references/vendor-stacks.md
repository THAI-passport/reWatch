# Vendor stack signatures (reference for re-watch-targets)

Recognition hints only. Every row is `[W]` (public documentation or common knowledge, not verified against your target) unless marked `[U]`. Confirm in the app you are analysing and re-tag in the target's FACTS.md and PROTOCOL.md. Package names are what to grep for; exact class names vary by SDK version.

## Signatures
| Stack | App-side signs | GATT signs | OTA / file layer | Notes |
|---|---|---|---|---|
| Jieli (JL) | `libjl_*` natives, `com.jieli.*` | 0xAE00 (0xAE01 write, 0xAE02 notify) | `jl_bt_ota`; an OTA service 0xAE10 is reported for budget watches (docs/SOP.md) | see `re-jieli` |
| Nordic nRF5 (legacy SDK) | `no.nordicsemi.android.dfu` | Secure DFU 0xFE59; legacy DFU 00001530-1212-EFDE-1523-785FEABCD123; Nordic UART 6E400001-B5A9-F393-E0A9-E50E24DCCA9E | DFU init packet + firmware image in a zip | buttonless DFU is a write that reboots into the bootloader: never send |
| Nordic nRF Connect SDK / Zephyr | `io.runtime.mcumgr`, `no.nordicsemi.android.mcumgr` | SMP service 8D53DC1D-1DB7-4CD3-868B-8A527460AA84 | mcumgr image upload, CBOR payloads | SMP also has read-only groups (image list, OS echo); the image and fs groups write |
| Realtek | `com.realsil.sdk.*`, `com.realtek.*` | vendor 128-bit services [U] | Realtek DFU library | data and OTA services differ per SDK [U] |
| Telink | `com.telink.*` | OTA service with base 00010203-0405-0607-0809-0a0b0c0d1912 (verify) | Telink OTA, sequential indexed packets with CRC | |
| Huami / Zepp (Amazfit, Mi Band) | `com.huami.*`, `com.xiaomi.*` | 0xFEE0 and 0xFEE1 | firmware and watch faces over a vendor chunked transfer | AES auth with a per-device key from the vendor account at pairing; never obtain it from the user's account |
| Bluetrum (AB5xxx) | vendor SDK packages [U] | OTA service 0x18A8 reported (docs/SOP.md) | OTA reported without bounds checks: hard-blacklist | |
| Actions (ATS) | `com.actions.*` [U] | [U] | [U] | |
| Bestechnic (BES) | `com.bes.*` [U] | [U] | [U] | mostly earbuds and some watches |
| Goodix, Dialog/Renesas, Ambiq | SDK package names in the app | [U] | [U] | treat as unknown until read |

## Protobuf-heavy ecosystems
Huami/Zepp (newer generations), Xiaomi, Huawei and Garmin are widely reported to wrap commands in Protocol Buffers or nested TLV instead of fixed offsets [W]. Look for `com.google.protobuf`, generated `*Proto` classes, or nanopb symbols in natives; then follow `re-protocol-spec` section "Protobuf and TLV".

## Read-only safe probes per stack
- Nordic SMP: OS echo and image state list are reads; image upload, erase, reset and fs write are not.
- Any stack: anything named ota, dfu, upgrade, firmware, erase, format, reset is outside the budget. Record the ids; never send.
