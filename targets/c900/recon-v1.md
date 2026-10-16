# C900 / Hiwear Plus — recon v1 (consolidated)

Snapshot of static recon through 2026-10-13 (Asia/Saigon). **Superseded in part by [recon-v2.md](recon-v2.md) (Phase 1 results); read v2 first.**  
Source of truth for detail remains PROTOCOL.md / FACTS.md; this file is the **starting brief** for plan review and subagents.  
Tags: [C] app code · [V] vector against code · [H] hardware · [W] third party · [I] inferred · [U] unknown · [owner] owner statement (not an AGENTS.md tag; treat as [W] for evidence weight, never as [C]/[H]).

---

## 1. Package and pin

| Finding | Tag | Source |
|---|---|---|
| Companion is Hiwear Plus `com.myled.HiwearPlus`, not HryFine / HiWatch Pro | [owner] + [W] listings | FACTS §1; TARGET.md |
| Pinned version 2.0.1, version code 31 | [C] | SOURCES.md |
| XAPK SHA-256 `5fa761a4d16ae8980fc40a341264441fe042858876ce1267dab54bd5be7b8952` | [C] | SOURCES.md |
| Base APK `931efc777ec58bc408e056da31f4e85af253a0fd35dafb6e901589829fe43a5a`; ABI `4c71b2819c5403cd8748931e6d24764b92ca518e677465820cb3469bf4ab7330` | [C] | SOURCES.md |
| Owner-approved repo copy zip `resources/c900/hiwear-plus-2.0.1.xapk.zip` (Git LFS), zip SHA `800662003d57aa272e5f829908c4c7671d1118ac4ed564242a5edcd4ca8e570e` | [owner] + [C] | SOURCES `REPO_COPY`; resources/README.md |
| Vendor Shenzhen United Power / lianhezhuli; packages `com.lhzl.*` | [W]/[C] | PROTOCOL §1 |

## 2. Stack (Bluetrum, not Jieli)

| Finding | Tag | Source |
|---|---|---|
| BLE stack: welie BLESSED | [C] | PROTOCOL §1; `com.welie.blessed` |
| No Jieli (`com.jieli`, `libjl_*`), no Realtek/Nordic-DFU/Telink SDK in app | [C] | PROTOCOL §1 (package/lib search) |
| Bluetrum tooling: `abpartool` / `ParTool.rawToPar`; Cus5610 path on service **0x18A8** | [C] | PROTOCOL §1; `com.bluetrum.abpartool.ParTool`; `ble/ota/Cus5610*` |
| Exact SoC on the C900 | [U]/[I] Bluetrum family | FACTS §1 |
| Beambox-style watch tag 0xB9 absent | [C] | PROTOCOL §1 |
| Shared OTA host path `api/hry/...` with HryFine naming | [C] → [I] shared vendor SDK | PROTOCOL §1, §8 |

## 3. Transports

| Finding | Tag | Source |
|---|---|---|
| Command/data: NUS-like `6E400001-B5A3-F393-E0A9-E50E24DCCA9F` write `...0002` notify `...0003` (without response) | [C] | `BleConstants`; PROTOCOL §2 |
| Battery 0x180F / 0x2A19; Device info 0x180A (firmware/hardware/platform/function) | [C] | PROTOCOL §2 |
| Generic OTA **0xFF00** (FF01/FF02/FF03) — never touch from client | [C] | PROTOCOL §2, §6 |
| Bluetrum 5610 OTA **0x18A8** — never touch | [C] | PROTOCOL §2 |
| Extra OTA UUID ending `...DCCA9E` — never touch | [C] | PROTOCOL §2 |
| Normal MTU 32; DFU 450; OTA tool path 185; app writes 20-byte pieces @ 20 ms | [C] | PROTOCOL §3; `MBleManager` / OTAUtils |
| Scan: MAC+`12:34` (or `56:10` DFU) in scan record, or name prefix `B0`/`H2`/`HY` | [C] | `BleScanActivity`; PROTOCOL §3 |
| C900 advertised name on air | [U] | needs HW-2 |

## 4. Frame (command channel)

| Finding | Tag | Source |
|---|---|---|
| App→watch: `DF \| len(2) \| sum \| cmd \| 01 \| key \| plen(2) \| payload` | [C] | `IssuedUtil`; PROTOCOL §4 |
| len = payload+5; total = len+4 | [C] | PROTOCOL §4 |
| sum = Σ(all bytes with sum slot 0) mod 256 | [C]/[V] | PROTOCOL §4, §9; `client/c900/frames.py` tests |
| Ack: `FD 00 05 sum cmd key x x status` (status 1 = ok) | [C] | `AckPackageConfigUtils`; PROTOCOL §4 |
| One command in flight; 100 s ack timeout → disconnect | [C] (jadx; smali check of the literal still owed, see Q04) | PROTOCOL §4 |
| Worked vector settings query: `df0005ee0901000000` | [V] | PROTOCOL §9 |

## 5. Commands (high level)

| Finding | Tag | Source |
|---|---|---|
| CommandID: OTA 0x01, SETTING 0x02, BIND 0x03, UNBIND 0x04, SPORT 0x05, RESET 0x06, FACTORY_TEST 0x07, DEVICE_SETTING 0x09, WATCH_FACE 0x0F, OTA_NEW 0x13, RESTORE 0x0D, … | [C] | `CommandID.smali` / `.java`; FACTS §4 |
| Time sync: cmd 0x02 key 1; 4-byte pack; year offset **−0x7d0** (−2000) | [C] | `SettingIssuedUtils.settingSysTime` smali; results/S2 |
| Message push cmd 0x02 key 18; find watch key 11; camera key 12 | [C] | PROTOCOL §5 |
| Dangerous: 0x01, 0x04, 0x06, 0x07, 0x0D, 0x13 | [C] | CommandID; FACTS §4 |
| Client codec blocklist matches that set | [C] | `client/c900/frames.BLOCKED_CMDS` |
| Many setting keys / health inbound payloads still incompletely tabulated | [U]/partial [C] | PROTOCOL §5, §7; OPEN-QUESTIONS Q4–Q5 |

## 6. OTA / watch-face (document only)

| Finding | Tag | Source |
|---|---|---|
| Store dial `.bin` is obfuscated Base64 text (`StringUtils.decodeInfo`), optional header trim, then `OTAUtils(main=5, sub=1)` on 0xFF00 | [C] | `DialDetailActivity`; PROTOCOL §6.1 |
| DIY face: `ParTool.rawToPar(...)` → `OTAUtils(main=2, sub=1)` | [C] | `WatchFaceEditActivity`; PROTOCOL §6.2 |
| Contacts sync: `OTAUtils(main=4, sub=1)` | [C] | `ContactActivity`; PROTOCOL §6 |
| OTA control `D5` / data `D6`; CRC left-shift poly 0x31; ready fun 0x81 carries MTU/interval/groupPacNum | [C] | `CommandUtils`, `OTAUtils`, `OTANotifyWriteUtils`; PROTOCOL §6.3 |
| OTA timing: 60 s overall timeout; ready reply carries deviceMtu, sendInterval (default 300 ms if 0), groupPacNum, timeout units x5000 ms | [C] first pass | PROTOCOL §6.3; verify in Q07 |
| Cus5610 on 0x18A8 is a **separate** DFU path, not used for dial push | [C] | PROTOCOL §6.4 |
| Exact PAR container bytes | [U] | native lib; OPEN-QUESTIONS Q11 |
| Face/firmware upload from our client | not done — deferred | PLAN Phase 4 |

## 7. Server inventory (summary)

| Finding | Tag | Source |
|---|---|---|
| Retrofit ~70 endpoints: account, `member_devices/bind_mac`, dial list/detail/download census, OTA `api/hry/get_update` + finish/error, weather hosts, privacy pages | [C] inventory | PROTOCOL §8 |
| No secrets / signed URLs recorded | policy | AGENTS.md |
| Full table still expandable | partial | OPEN-QUESTIONS Q9 |

## 8. Gemini document verdict

Source kept as untrusted data: `targets/c900/sources/gemini-hiwear-re.md`. Disputes: FACTS §2.

| Topic | Verdict |
|---|---|
| Header DF, checksum rule, FD ack layout | Confirmed [C] |
| Opcodes (time 0x02/0x0A, info 0xF3, find 0x07, face via 0x04, …) | **Wrong** [C]; 0x04/0x07 dangerous |
| FF00 as “command service”, MTU 512 | **Wrong** [C] |
| Dial magic ZL/AB_DIAL layout | [U] / not confirmed in Java |

---

## Decisions from findings

| ID | Finding | Decision | Rationale |
|---|---|---|---|
| D-stack | No Jieli in app; Bluetrum abpartool + 0x18A8 | **Deprioritise re-jieli / Jieli playbooks** for C900; use Bluetrum/United Power notes | Wrong skill family wastes passes |
| D-face | Faces/contacts/paper ride OTAUtils on 0xFF00 (D5/D6), not DF cmd alone | Treat face upload as **OTA-class**; defer to PLAN Phase 4 + design review; never wire into client now | Brick/flash risk; ground rule 7 |
| D-block | CommandID lists OTA/unbind/reset/factory/restore | Enforce **BLOCKED_CMDS** `{0x01,0x04,0x06,0x07,0x0D,0x13}` in codec; never send | Prevents Gemini-style mistakes on hardware |
| D-client | Protocol map incomplete; no [H] yet | **Defer client features** (G4 / PLAN Phase 3); keep codec sketch only | Plan-first; avoid implementing the wrong API |
| D-lfs | Cloud agents need rebuild without floating CDN | Keep **one** owner-approved LFS zip + REPO_COPY; CI without `lfs:true`; `git lfs pull -I` only that path | ~102 full pulls/month on Free bandwidth |
| D-phase0 | Deeper decompile before goals clear wastes tokens/LFS | **Phase 0 gate**: approve PLAN + OPEN-QUESTIONS before Phase 1 static deepen | Owner feedback 2026-10-13 |
| D-identity | Owner named Hiwear Plus; landscape assumed HryFine | One target `c900`; fold legacy combined docs into sources/ | Stop cross-contaminating FACTS |
| D-order | P0 questions need the watch; P1 are static | Run approved **static** P1 questions first; P0 hardware only after HW-0 run sheet + per-session approval. Priority = importance, not run order | Software first, hardware last (AGENTS.md) |
| D-capture | Owner may already hold an HCI snoop (HW-1) | Ask owner for an existing capture before any live probe (new C900-Q13) | An existing capture is software, needs no watch contact |
| D-gemini | Third-party RE mixed right framing with wrong opcodes | Keep as annotated source; opcodes only from CommandID/[C] | Safety |


---

## Review notes (improve-plan pass 2026-10-12)

- No new [C] claims were added in this pass; decompiled tree was not present and not bootstrapped.
- Weakest tags to firm up in Phase 1: 100 s ack timeout (jadx literal), MTU 32 vs 20-byte pieces (both [C], but which governs on the C900 is [U] until [H]), OTA ready-reply field widths.
- recon-v1 has no inbound (watch -> app) findings table; inbound is only a sketch (PROTOCOL §7, results/S5). That gap is C900-Q05.
