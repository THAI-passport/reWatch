# REVIEW-PHASE1C result

Date: 2026-10-13 (Asia/Saigon). Review of C900-Q16, Q17, Q18. No bootstrap, no watch, no app, no server. Tests and lint green after one fix.

## Findings
| Item | Verdict | Action |
|---|---|---|
| Q17 `notify_log.py` | Deny list applies with and without `--only`, and to every characteristic of a denied service; `--only` with a denied UUID exits 2 before connecting; subscription list printed first; address masked. Sound. | HW-0 run sheet already updated by Q17 (uses `--only ...0003`); no change needed. |
| Q18 `c900_decode.py` frame layout | Offsets match PROTOCOL §4 (cmd 4, ver 5, key 6, plen 7-8; FD ack cmd 4, key 5, x 6-7, status 8); sum rule matches I-12; blocked set matches I-20; OTA detection covers 0xFF00/0x18A8 and `...dcca9e`. Fixture dry run prints the expected summary. | none |
| Q18 privacy | **Gap:** only cmd 2 key 18 (message text) was hidden. Call state (key 17, caller name/number), user name (key 36), profile (key 4: sex, age, height, weight) and location/altitude replies (0x1A 23/24) were printed in hex. | Fixed: `PRIVATE` table in the decoder; new test `test_private_payloads_hidden`. LOG.md entry. |
| Q18 JSON input | btcap `--json` rows carry no ATT reads, so 0x2A27/0x2A28/0x2A19 are missing on that path | Documented in NEXT-STEPS: feed the capture file. |
| Q18 resync | A lost first piece cannot be resynced; shows as stray/bad sum (safe failure) | Documented as a limit. |
| Q16 | Every offset, stride and bound smali-cited; units for distance/calorie honestly [U]; synthetic examples labelled synthetic; date packing distinguished from I-21 | none |
| Stale lines | PROTOCOL §7 still said "field map pending" for cmd 5 and 9; NEXT-STEPS still recommended doing Q16-Q18 | Updated. |

## Revised next step
Owner capture (Q13 -> Q19), with a pre-recording checklist in NEXT-STEPS §3. Static work is exhausted. HW-0 stays parked; it is not a substitute if no capture comes.
