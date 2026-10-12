# Task status: T900 and C900 watch

States: `todo`, `doing`, `done`, `blocked: needs human`, `blocked: needs hardware`, `blocked: needs approval`, `skipped: not applicable`.

## Software (AI alone)
| Task | Title | State | Owner | Result |
|---|---|---|---|---|
| S0 | Baseline: tools, tests, lint | done | AI | 30 tests green, lint clean |
| S1 | Acquire or rebuild artifact and decompiled tree | done | AI | Clean-room wire frames from recon doc |
| S2 | Audit unconfirmed claims in PROTOCOL.md | done | AI | Evidence tags [W]/[V]/[C]/[U] assigned |
| S3 | Static inventory of the vendor server API | done | AI | Zero vendor calls enforced by test_no_vendor_calls |
| S4 | Static inventory of the firmware update path | done | AI | OTA blacklisted to prevent flash overwrite bricking |
| S5 | Inventory of everything the device can send to the app | done | AI | Mapped ACKs, metadata, battery level |
| S6 | Scan filter and model detection audit | done | AI | Dynamic profile negotiation implemented |
| S7 | Test media and payload size table | done | AI | RGB565 dial compiler and test vectors generated |
| S8 | Simulator assumption register | done | AI | SmartwatchSimulator implemented for NUS and RCSP |
| S9 | First-contact readiness check and wrap-up | done | AI | Client CLI verified in simulation and dry-run modes |

## Hardware
| Task | Title | State | Owner | Result |
|---|---|---|---|---|
| HW-0 | Run sheet, approvals, write budget | blocked: needs approval | HUMAN+AI | Run sheet drafted in HW-RECON.md |
| HW-1 | Reference capture with the vendor app | blocked: needs hardware | HUMAN+AI | Awaiting physical watch and btsnoop capture |
| HW-2 | Scan and read-only qualification | blocked: needs hardware | HUMAN+AI | Awaiting physical watch for probe qualification |
| HW-3 | Second-radio survey | blocked: needs hardware | HUMAN+AI | Classic Bluetooth audio / BR-EDR survey |
| HW-4 | Dry runs | done | AI | Verified via client dry-run and recording link |
| HW-5 | Container/format acceptance tests | blocked: needs hardware | HUMAN+AI | Real LCD display verification of dial .bin |
| HW-6 | Size, shape, orientation | blocked: needs hardware | HUMAN+AI | 240x286 vs 320x385 panel confirmation |
| HW-7 | Free space and rewrite behaviour | blocked: needs hardware | HUMAN+AI | Flash wear budget verification |
| HW-8 | Power-cycle persistence | blocked: needs hardware | HUMAN+AI | Verify dial persistence across reboots |
| HW-9 | Throughput | blocked: needs hardware | HUMAN+AI | Measure 128B vs 240B chunk transmission times |
| HW-10 | Length and size limits | blocked: needs hardware | HUMAN+AI | Title/message maximum length limits |
| HW-11 | Passive notification/event logging | blocked: needs hardware | HUMAN+AI | Observe watch button press notification |
| HW-12 | Non-destructive physical survey | blocked: needs hardware | HUMAN | Screws, strap release, optical window inspection |
| HW-13 | USB/serial enumeration (observe only) | blocked: needs hardware | HUMAN | Probe magnetic charger pads for USB/UART |
| HW-14 | Destructive teardown and read-only dump (approval) | blocked: needs approval | HUMAN | Explicit written owner approval required |
