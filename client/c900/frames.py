"""C900 frame codec, BUILT AHEAD of the artifact.

Every layout here comes from a third-party write-up (docs/recon/budget-smartwatch-landscape.md,
section 3.2) and is [W]. Nothing is confirmed. Uncertain values are named constants so the first
code read or capture needs constant changes, not rewrites. See targets/c900/PROTOCOL.md and FACTS.md.
"""

APP_HEADER = 0xDF      # [W]
ACK_HEADER = 0xFD      # [W], disputed in FACTS.md
FIXED_BYTE = 0x01      # [W] byte 5 of an app frame
LEN_OFFSET = 4         # [W] total length = Len + LEN_OFFSET; meaning of Len disputed in FACTS.md
CHECKSUM_INDEX = 3     # [W]

CMD_TIME, SUB_TIME = 0x02, 0x0A      # [W]
CMD_INFO, SUB_INFO = 0xF3, 0x00      # [W]


def checksum(frame):
    """Sum mod 256 of the whole frame with the checksum byte taken as zero [W]."""
    return (sum(frame) - frame[CHECKSUM_INDEX]) & 0xFF


def build(cmd, sub, payload=b""):
    if len(payload) > 0xFFFF:
        raise ValueError("payload too long")
    body = bytes([cmd, FIXED_BYTE, sub]) + len(payload).to_bytes(2, "big") + bytes(payload)
    total = 4 + len(body)
    n = total - LEN_OFFSET
    f = bytearray([APP_HEADER, n >> 8, n & 0xFF, 0]) + body
    f[CHECKSUM_INDEX] = checksum(f)
    return bytes(f)


def parse(frame):
    """Return (header, cmd, sub_or_key, payload). Raises ValueError on a bad frame."""
    if len(frame) < 9 or frame[0] not in (APP_HEADER, ACK_HEADER):
        raise ValueError("bad header or short frame")
    if ((frame[1] << 8) | frame[2]) + LEN_OFFSET != len(frame):
        raise ValueError("length mismatch")
    if checksum(frame) != frame[CHECKSUM_INDEX]:
        raise ValueError("checksum mismatch")
    plen = int.from_bytes(frame[7:9], "big")
    if frame[0] == ACK_HEADER:
        return frame[0], frame[4], frame[5], bytes(frame[9:])
    return frame[0], frame[4], frame[6], bytes(frame[9:9 + plen])


def ack(cmd, key=0):
    """Watch acknowledgement as the write-up describes it [W]: FD 00 05 chk cmd key 00 01 01."""
    f = bytearray([ACK_HEADER, 0x00, 0x05, 0, cmd, key, 0x00, 0x01, 0x01])
    f[CHECKSUM_INDEX] = checksum(f)
    return bytes(f)


class SimWatch:
    """Software watch for tests. Proves consistency with this codec only, never the real device."""

    def __init__(self):
        self.received = []

    def write(self, data):
        hdr, cmd, sub, payload = parse(data)
        self.received.append((cmd, sub, payload))
        return ack(cmd)
