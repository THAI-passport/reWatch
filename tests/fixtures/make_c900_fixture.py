#!/usr/bin/env python3
"""Build tests/fixtures/c900_synthetic.btsnoop: a made-up C900 session for tools/c900_decode.py tests.

SYNTHETIC: every byte is invented from PROTOCOL.md layouts; no vendor capture, device or person is involved. The MAC is a
locally administered fake (02:00:00:00:00:01). Regenerate: python tests/fixtures/make_c900_fixture.py
"""
import os
import struct

BASE_TS = 0x00dcddb30f2f8000 + 1_700_000_000_000_000
CONN = 0x0040
UUID128 = lambda s: bytes.fromhex(s.replace("-", ""))[::-1]  # noqa: E731
H = {"w": 0x0010, "n": 0x0012, "ota": 0x0030, "bat": 0x0020, "hw": 0x0022, "fw": 0x0024, "feat": 0x0026}


def frame(hdr, cmd, mid, key, payload=b""):
    """mid = ver for DF; for FD the layout is cmd key x_hi x_lo status (payload ignored)."""
    if hdr == 0xFD:
        body = bytes([cmd, key]) + payload
    else:
        body = bytes([cmd, mid, key]) + len(payload).to_bytes(2, "big") + payload
    n = len(body)
    f = bytearray([hdr, n >> 8, n & 0xFF, 0]) + body
    f[3] = (sum(f) - f[3]) & 0xFF
    return bytes(f)


def att(op, *parts):
    return bytes([op]) + b"".join(parts)


def pkt(att_pdu):
    l2 = struct.pack("<HH", len(att_pdu), 4) + att_pdu
    return b"\x02" + struct.pack("<HH", CONN | (2 << 12), len(l2)) + l2


def build():
    recs = []
    t = [0]

    def add(direction, pdu):
        t[0] += 5000
        recs.append((direction, pkt(pdu)))

    def decl(h, uuid16=None, uuid=None):
        return struct.pack("<HBH", h - 1, 0x10, h) + (struct.pack("<H", uuid16) if uuid16 else UUID128(uuid))

    # discovery (read-by-type responses with characteristic declarations): 16-bit set, then 128-bit set
    add("rx", att(0x09, bytes([7]), decl(H["bat"], 0x2A19), decl(H["hw"], 0x2A27), decl(H["fw"], 0x2A26), decl(H["feat"], 0x2A28)))
    add("rx", att(0x09, bytes([21]), decl(H["w"], uuid="6e400002-b5a3-f393-e0a9-e50e24dcca9f"),
                  decl(H["n"], uuid="6e400003-b5a3-f393-e0a9-e50e24dcca9f"), decl(H["ota"], uuid="6e40ff03-b5a3-f393-e0a9-e50e24dcca9e")))
    feat = bytearray(26)
    feat[0], feat[1], feat[15], feat[25] = 0xAA, 0x80, 0x40, 0x80
    for h, v in ((H["hw"], b"V1.2"), (H["fw"], b"SYN-0.0.1"), (H["feat"], bytes(feat)), (H["bat"], bytes([77]))):
        add("tx", att(0x0A, struct.pack("<H", h)))
        add("rx", att(0x0B, v))
    w = lambda f: add("tx", att(0x52, struct.pack("<H", H["w"]), f))  # noqa: E731
    n = lambda f: add("rx", att(0x1B, struct.pack("<H", H["n"]), f))  # noqa: E731
    w(frame(0xDF, 0x03, 1, 0))                                       # bind
    n(frame(0xFD, 0x03, 0, 0, b"\x00\x00\x01"))                      # ack
    w(frame(0xDF, 0x02, 1, 1, bytes([0x6B, 0x5A, 0xA7, 0x8F])))      # time sync (made-up date)
    n(frame(0xFD, 0x02, 0, 1, b"\x00\x00\x01"))
    msg = frame(0xDF, 0x02, 1, 18, b"\x01\x00\x00" + b"synthetic:test message")
    w(msg[:20]); w(msg[20:])                                          # two pieces  # noqa: E702
    spo2 = frame(0xDF, 0x05, 1, 14, bytes([0x1B, 0x2A, 0, 0, 0, 0, 0xA8, 0xC0, 0, 0, 0, 97]))
    n(spo2[:10]); n(spo2[10:])                                        # split notify  # noqa: E702
    n(frame(0xDF, 0x0C, 1, 2))                                        # camera shutter
    n(frame(0xDF, 0x0C, 1, 19))                                       # bond request
    n(frame(0xDF, 0x0E, 1, 1, bytes([0x02, 0, 0, 0, 0, 0x01])))       # classic MAC (fake)
    bad = bytearray(frame(0xDF, 0x0C, 1, 1)); bad[3] ^= 0xFF; n(bytes(bad))  # bad sum  # noqa: E702
    w(frame(0xDF, 0x04, 1, 0))                                        # unbind: blocked cmd, to test the flag
    add("rx", att(0x1B, struct.pack("<H", H["ota"]), b"\x00\x01"))    # OTA notify: must be flagged, not decoded
    out = bytearray(b"btsnoop\x00" + struct.pack(">II", 1, 1002))
    ts = BASE_TS
    for direction, p in recs:
        ts += 5000
        out += struct.pack(">IIIIQ", len(p), len(p), 1 if direction == "rx" else 0, 0, ts) + p
    return bytes(out)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "c900_synthetic.btsnoop")
    open(path, "wb").write(build())
    print(path)
