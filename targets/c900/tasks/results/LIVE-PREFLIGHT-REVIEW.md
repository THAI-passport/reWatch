# Review of the 2026-10-13 live pre-flight (INCIDENT-2026-10-13-LIVE-BLUETOOTH-PREFLIGHT.md)

Date 2026-10-13 (Asia/Saigon). Reviewer: Claude, from the committed incident file and the owner's transcript, read as untrusted data. No radio touched from here.

## 1. Was live session 1 done?
**No.** No BLE scan, connect, read or listen completed. The only data came from `system_profiler SPBluetoothDataType` on the owner's Mac (a host-side read of the OS pairing table). The one probe attempt (`scan --seconds 3`, started by an agent in a background shell) hung before discovery and was killed. LIVE-SESSION-1 section 0 is still entirely open.

## 2. What was actually learned
| Fact | Tag | Note |
|---|---|---|
| The watch exposes a Classic BR/EDR identity named `Watch Ultra`, vendor id 0x0642, product id 0x0220, firmware string `0.0.1`, profiles HFP, AVRCP, A2DP, HID | [H] (owner's Mac, system_profiler) | First hardware evidence. Whether `Watch Ultra` is also the BLE advertised name is [U] (Q01 still open) |
| The Mac is **paired and connected** to the watch over Classic | [H] | LIVE-SESSION-1 go/no-go box "Mac has never been paired" is now unticked: session 1 is **no-go** until the owner decides (section 4) |
| An agent shell without macOS Bluetooth (TCC) permission blocks in CoreBluetooth instead of failing | [H] (sample of the hung process, `CBManager.authorization() == 0`) | Probe should fail fast; FIXES Open |
| HID profile present | [H] | Expected for a watch with media keys / camera shutter [I]; not suspicious by itself |

## 3. Anti-RE: what was found, and what the incident file got wrong
**No anti-RE or malicious measure was observed.** Nothing the watch sent was seen at all on BLE. The incident's "trap matrix" lists generic threats, not observations; each "Defended" there means "the probe has a rule for it", not "it happened". Corrections:
- "Bluetrum AB56xx and JieLi JL70xx" and "JieLi `0000AE00`": the C900 app is Bluetrum, no Jieli (INVARIANTS I-02 [C]). Do not load the Jieli playbook.
- "all inbound strings sanitized to printable ASCII": wrong. `sanitize` removes control and format characters and caps length; non-ASCII printable text stays.
- "BLE advertised as `C900`/`Hiwear`" and "`C900 Audio`" names: invented examples; the BLE name is [U].
- "Classic vs BLE trap": not a trap, normal dual-mode design. It does matter for addressing: on macOS the probe needs the BLE CoreBluetooth UUID from its own scan, never the Classic MAC from system_profiler.
- Privacy: the committed file contained the Mac controller's full Bluetooth address; masked in this commit. It remains in git history (commit 3d1b298); rewriting a shared branch's history needs the owner's decision.

## 4. Decision needed: the Mac is now paired with the watch
Risks of probing while paired [I]: dual-mode chips can derive LE keys from the Classic bond (cross-transport key derivation), so an LE connection may come up encrypted and bonded to the Mac without any dialog; the probe cannot see bond state on macOS. The phone may also lose calls/audio while the Mac holds the Classic link.

| Option | Effect |
|---|---|
| A (recommended): owner opens System Settings, Bluetooth, `Watch Ultra`, **Disconnect** (not Forget), turns the watch's Bluetooth/phone link back to normal, records it | Mac keeps its pairing record, Classic link idle; session 1 still formally no-go but owner may waive the box in writing with this risk noted |
| B: owner chooses **Forget This Device** on the Mac | Removes the Mac's keys only; does not unbind the watch from Hiwear Plus [I]; then the box can be ticked again. The watch may keep a stale key for the Mac [I] |
| C: capture first (NEXT-STEPS section 4b) | No Mac involvement; recommended order anyway |

The probe and the plan never unpair or forget devices; that is the owner's call.

## 5. Rules confirmed for agents
- An AI agent does not start the probe; the owner runs it in an interactive Terminal that has Bluetooth permission. A hang without permission is expected behaviour, not a watch trick.
- Logs and pastes mask every Bluetooth address (watch and Mac) as `XX:XX:XX:XX:AB:CD` or fully.
