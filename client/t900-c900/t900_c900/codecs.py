"""Pure protocol codecs for HryFine (NUS) and JieLi (RCSP) wire frames."""
import datetime
from typing import Any, Dict, Optional, Tuple


def calc_hryfine_checksum(frame: bytes | bytearray) -> int:
    """Calculate Modulo-256 sum of all bytes in frame with byte[3] set to 0."""
    total = sum(frame[:3]) + 0
    if len(frame) > 4:
        total += sum(frame[4:])
    return total & 0xFF


def build_hryfine_frame(cmd: int, sub: int, payload: bytes = b"", key: int = 0x01) -> bytes:
    """Build an App-to-Watch HryFine 0xDF frame."""
    pay_len = len(payload)
    pay_hi = (pay_len >> 8) & 0xFF
    pay_lo = pay_len & 0xFF
    inner = bytes([cmd, key, sub, pay_hi, pay_lo]) + payload
    inner_len = len(inner)

    len_hi = (inner_len >> 8) & 0xFF
    len_lo = inner_len & 0xFF

    frame = bytearray([0xDF, len_hi, len_lo, 0x00]) + inner
    frame[3] = calc_hryfine_checksum(frame)
    return bytes(frame)


def build_hryfine_ack(cmd: int, status: int = 0x01, key: int = 0x01) -> bytes:
    """Build a Watch-to-App HryFine 0xFD acknowledgement frame."""
    inner = bytes([cmd, key, 0x00, 0x01, status])
    frame = bytearray([0xFD, 0x00, 0x05, 0x00]) + inner
    frame[3] = calc_hryfine_checksum(frame)
    return bytes(frame)


def parse_hryfine_frame(data: bytes) -> Dict[str, Any]:
    """Parse and validate a HryFine wire frame (0xDF or 0xFD)."""
    if len(data) < 4:
        raise ValueError("Frame too short for header")
    magic = data[0]
    if magic not in (0xDF, 0xFD):
        raise ValueError(f"Invalid magic byte: 0x{magic:02X}")

    length = (data[1] << 8) | data[2]
    expected_total = length + 4
    if len(data) < expected_total:
        raise ValueError(f"Incomplete frame: expected {expected_total} bytes, got {len(data)}")

    checksum = data[3]
    calc_sum = calc_hryfine_checksum(data[:expected_total])
    if checksum != calc_sum:
        raise ValueError(f"Checksum mismatch: got 0x{checksum:02X}, expected 0x{calc_sum:02X}")

    if magic == 0xDF:
        if length < 5:
            raise ValueError("Inner packet too short for 0xDF command header")
        cmd = data[4]
        key = data[5]
        sub = data[6]
        pay_len = (data[7] << 8) | data[8]
        payload = data[9:9 + pay_len]
        return {
            "type": "command",
            "magic": magic,
            "cmd": cmd,
            "key": key,
            "sub": sub,
            "payload": payload,
        }
    else:  # 0xFD ACK
        if length < 5:
            raise ValueError("Inner packet too short for 0xFD ACK header")
        cmd = data[4]
        key = data[5]
        ack_len = (data[6] << 8) | data[7]
        status = data[8]
        return {
            "type": "ack",
            "magic": magic,
            "cmd": cmd,
            "key": key,
            "ack_len": ack_len,
            "status": status,
        }


def build_time_sync(dt: Optional[datetime.datetime] = None) -> bytes:
    """Build HryFine Time Synchronization command (Cmd 0x02, Sub 0x0A)."""
    if dt is None:
        dt = datetime.datetime.now()
    year = dt.year
    payload = bytes([
        (year >> 8) & 0xFF,
        year & 0xFF,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
    ])
    return build_hryfine_frame(cmd=0x02, sub=0x0A, payload=payload)


def build_metadata_query() -> bytes:
    """Build HryFine Device Metadata query command (Cmd 0xF3, Sub 0x00)."""
    return build_hryfine_frame(cmd=0xF3, sub=0x00, payload=b"")


def build_notification_alert(app_id: int, title: str, message: str) -> bytes:
    """Build HryFine push notification alert (Cmd 0x05, Sub 0x01)."""
    title_bytes = title.encode("utf-8")[:32]
    msg_bytes = message.encode("utf-8")[:128]
    payload = bytes([app_id, len(title_bytes)]) + title_bytes + bytes([len(msg_bytes)]) + msg_bytes
    return build_hryfine_frame(cmd=0x05, sub=0x01, payload=payload)


def build_find_watch(alert: bool = True) -> bytes:
    """Build HryFine find-watch alert (Cmd 0x07, Sub 0x01)."""
    return build_hryfine_frame(cmd=0x07, sub=0x01, payload=bytes([0x01 if alert else 0x00]))


# --- JieLi RCSP Codecs ---

JIELI_HEADER = b"\xFE\xDC\xBA"
JIELI_TRAILER = b"\xEF"


def crc16_xmodem(data: bytes) -> int:
    """CRC-16/XMODEM calculation (poly 0x1021, init 0x0000). Check for b'123456789' is 0x31C3."""
    crc = 0x0000
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


# JieLi OTA runs over the normal 0xAE00 RCSP link, not a separate service: the
# official OTA SDK docs describe device-pulled firmware blocks with opcode 0xE5 [W].
# The neighbouring 0xE0-0xEF range is blocked as a whole until the app's OTA command
# table is read [I]. No code path may build or send these frames.
PROHIBITED_RCSP_OPCODES = frozenset(range(0xE0, 0xF0))


def is_rcsp_ota_frame(data: bytes) -> bool:
    """True if data is (the first chunk of) an RCSP frame carrying an OTA opcode."""
    return len(data) >= 5 and data[:3] == JIELI_HEADER and data[4] in PROHIBITED_RCSP_OPCODES


def build_jieli_frame(flag: int, opcode: int, body: bytes) -> bytes:
    """Build a JieLi RCSP wire frame. Refuses OTA opcodes."""
    if opcode in PROHIBITED_RCSP_OPCODES:
        raise ValueError("HARD BLOCKED: RCSP opcode 0x%02X is in the OTA range" % opcode)
    body_len = len(body)
    header = JIELI_HEADER + bytes([flag, opcode, (body_len >> 8) & 0xFF, body_len & 0xFF])
    return header + body + JIELI_TRAILER


def parse_jieli_frame(data: bytes) -> Dict[str, Any]:
    """Parse and validate a JieLi RCSP wire frame."""
    if len(data) < 8:
        raise ValueError("Data too short for JieLi frame")
    if not data.startswith(JIELI_HEADER):
        raise ValueError("Missing JieLi frame header (FE DC BA)")
    if not data.endswith(JIELI_TRAILER):
        raise ValueError("Missing JieLi frame trailer (EF)")

    flag = data[3]
    opcode = data[4]
    length = (data[5] << 8) | data[6]
    body = data[7:-1]
    if len(body) != length:
        raise ValueError(f"Body length mismatch: header says {length}, got {len(body)}")

    return {
        "flag": flag,
        "opcode": opcode,
        "length": length,
        "body": body,
    }
