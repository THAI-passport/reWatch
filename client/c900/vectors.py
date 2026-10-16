"""Shared byte vectors: the Python codec is the reference, the Kotlin core must match it.

    python -m client.c900.vectors > tests/fixtures/c900_vectors.json   (tests check it is current)
"""
import json

from client.c900 import frames

CASES = [
    # name, cmd, key, payload hex, ver; evidence in the comment
    ("settings_query", 0x09, 0x00, "", frames.DEFAULT_VER),                 # PROTOCOL section 9 [V]
    ("find_on_c900", 0x02, 0x0B, "01", frames.C900_VER),                    # LIVE-SESSION-2 [H]
    ("find_off_c900", 0x02, 0x0B, "00", frames.C900_VER),                   # PROTOCOL 5 key 11 [C]
    ("time_c900_q19", 0x02, 0x01, frames.time_payload(2026, 10, 13, 16, 23, 11).hex(), frames.C900_VER),  # C900-Q19 [H]
    ("message_sms", 0x02, 0x12, (bytes([1, 0, 0]) + b"reWatch:test").hex(), frames.C900_VER),
    ("hour12", 0x02, 0x1A, "01", frames.C900_VER),                          # I-22 [C]
]


def build_vectors():
    out = {"frames": [], "acks": [], "times": []}
    for name, cmd, key, p, ver in CASES:
        f = frames.build(cmd, key, bytes.fromhex(p), ver=ver)
        out["frames"].append({"name": name, "cmd": cmd, "key": key, "payload": p, "ver": ver, "frame": f.hex()})
        out["acks"].append({"name": name, "cmd": cmd, "key": key, "x": len(f),
                            "ack": frames.ack(cmd, key, x=len(f)).hex()})
    for t in [(2026, 10, 13, 16, 23, 11), (2000, 1, 1, 0, 0, 0), (2063, 12, 31, 23, 59, 59)]:
        out["times"].append({"t": list(t), "payload": frames.time_payload(*t).hex()})
    out["hw_revision"] = [{"raw": r, "ver": frames.ver_from_hw_revision(r.encode())} for r in ("10000", "V1.2", "v3", "", "HW-A")]
    return out


if __name__ == "__main__":
    print(json.dumps(build_vectors(), indent=1))
