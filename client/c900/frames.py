"""C900 frame codec for the Hiwear Plus 2.0.1 command channel.

Status 2026-10-13: **client feature work DEFERRED** (targets/c900/PLAN.md Phase 3). Layout, checksum, ack and opcodes are read from the app's code [C]
(targets/c900/PROTOCOL.md sections 4-6, smali of SettingIssuedUtils and CommandID). UNVERIFIED on
hardware: nothing here has been sent to a watch. build() refuses the dangerous command ids in
BLOCKED_CMDS (OTA, unbind, reset, factory test, factory restore).
"""

APP_HEADER = 0xDF      # [C]
ACK_HEADER = 0xFD      # [C]
FIXED_BYTE = 0x01      # [C] default ver byte (0-based index 5); the app overwrites it from the 0x2A27 major (I-10)
DEFAULT_VER = FIXED_BYTE
C900_VER = 0x10        # [H] C900 / Watch Ultra: 0x2A27 "10000" -> app sends 0x10 (C900-Q19, all 63 app frames)
LEN_OFFSET = 4         # [C] total length = Len + 4; Len counts cmd..payload (payload + 5)
CHECKSUM_INDEX = 3     # [C]

# Command ids, CommandID.smali [C]
CMD_SETTING = 0x02           # COMMAND_ID_SETTING_ORDER
CMD_BIND = 0x03              # COMMAND_ID_BANGLE_DEVICE
CMD_DEVICE_SETTING = 0x09    # COMMAND_ID_DEVICE_SETTING
CMD_WATCH_FACE = 0x0F        # COMMAND_ID_WATCH_FACE

# Keys under CMD_SETTING [C]
KEY_TIME, KEY_FIND, KEY_CAMERA, KEY_MESSAGE = 0x01, 0x0B, 0x0C, 0x12

# Dangerous ids [C]: OTA, unbind, reset, factory test, factory restore, OTA (new). Never built.
BLOCKED_CMDS = frozenset({0x01, 0x04, 0x06, 0x07, 0x0D, 0x13})

# Kept so old callers read the real values; the old [W] guesses (0x02/0x0A, 0xF3/0x00) were wrong.
CMD_TIME, SUB_TIME = CMD_SETTING, KEY_TIME
CMD_INFO, SUB_INFO = CMD_DEVICE_SETTING, 0x00


class BlockedCommand(ValueError):
    pass


def time_payload(year, month, day, hour, minute, second):
    """4 packed bytes as SettingIssuedUtils.settingSysTime builds them (smali: add-int/lit16 -0x7d0) [C].

    b0 = (year-2000)<<2 | month>>2; b1 = (month&3)<<6 | day<<1 | hour>>4;
    b2 = (hour&15)<<4 | minute>>2; b3 = (minute&3)<<6 | second. month is 1-12.
    """
    if not (2000 <= year < 2064 and 1 <= month <= 12 and 1 <= day <= 31
            and 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
        raise ValueError("time out of range")
    y = year - 2000
    return bytes([((y << 2) + (month >> 2)) & 0xFF,
                  (((month & 3) << 6) + (day << 1) + (hour >> 4)) & 0xFF,
                  (((hour & 15) << 4) + (minute >> 2)) & 0xFF,
                  (((minute & 3) << 6) + second) & 0xFF])


def checksum(frame):
    """Sum mod 256 of the whole frame with the checksum byte taken as zero [C]."""
    return (sum(frame) - frame[CHECKSUM_INDEX]) & 0xFF


def ver_from_hw_revision(raw):
    """ver byte the app derives from a 0x2A27 value: strip a leading V/v, integer before the first dot,
    truncated to a byte [C rule, C900-Q04; truncation seen on the wire, C900-Q19]. None if unreadable."""
    s = bytes(raw or b"").decode("ascii", "replace").strip()
    if s[:1] in ("V", "v"):
        s = s[1:]
    digits = s.split(".", 1)[0]
    if not digits.isdigit() or len(digits) > 9:
        return None
    return int(digits) & 0xFF


def build(cmd, sub, payload=b"", ver=DEFAULT_VER):
    if not (0 <= int(ver) <= 0xFF):
        raise ValueError("ver must be one byte")
    if cmd in BLOCKED_CMDS:
        raise BlockedCommand("command 0x%02X is on the dangerous-command blocklist" % cmd)
    if len(payload) > 0xFFFF:
        raise ValueError("payload too long")
    body = bytes([cmd, int(ver), sub]) + len(payload).to_bytes(2, "big") + bytes(payload)
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


def ack(cmd, key=0, x=1, status=1):
    """Acknowledgement FD 00 05 chk cmd key x_hi x_lo status [C layout]. The watch sets x to the total
    length of the frame it acknowledges and status 1 (I-18 [H], C900-Q19); the app's own ACK uses x=0,
    its NAK x=3 status 0 [C]."""
    if not (0 <= x <= 0xFFFF):
        raise ValueError("x must fit in 2 bytes")
    f = bytearray([ACK_HEADER, 0x00, 0x05, 0, cmd, key, x >> 8, x & 0xFF, status])
    f[CHECKSUM_INDEX] = checksum(f)
    return bytes(f)


class SimWatch:
    """Software watch for tests. Proves consistency with this codec only, never the real device."""

    def __init__(self, ver=DEFAULT_VER):
        self.received = []
        self.ver = ver
        self.vers = []

    def write(self, data):
        hdr, cmd, sub, payload = parse(data)
        self.received.append((cmd, sub, payload))
        self.vers.append(data[5])
        return ack(cmd, sub, x=len(data))  # watch behaviour seen in C900-Q19 [H]
