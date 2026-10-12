"""Unit tests for pure wire codecs and checksum validation."""
import datetime
import unittest
from t900_c900.codecs import (
    calc_hryfine_checksum,
    build_hryfine_frame,
    build_hryfine_ack,
    parse_hryfine_frame,
    build_time_sync,
    build_metadata_query,
    build_notification_alert,
    crc16_xmodem,
    build_jieli_frame,
    parse_jieli_frame,
)


class TestCodecs(unittest.TestCase):
    def test_hryfine_worked_example_metadata_query(self):
        # From PROTOCOL.md Example 1:
        # DF 00 05 D8 F3 01 00 00 00
        frame = build_metadata_query()
        self.assertEqual(frame.hex().upper(), "DF0005D8F301000000")
        parsed = parse_hryfine_frame(frame)
        self.assertEqual(parsed["cmd"], 0xF3)
        self.assertEqual(parsed["sub"], 0x00)
        self.assertEqual(parsed["payload"], b"")

    def test_hryfine_worked_example_time_sync(self):
        # From PROTOCOL.md Example 2:
        # Date: 2026-10-12 09:30:00
        # DF 00 0C 2D 02 01 0A 00 07 07 EA 0A 0C 09 1E 00
        dt = datetime.datetime(2026, 10, 12, 9, 30, 0)
        frame = build_time_sync(dt)
        self.assertEqual(frame.hex().upper(), "DF000C2D02010A000707EA0A0C091E00")
        parsed = parse_hryfine_frame(frame)
        self.assertEqual(parsed["cmd"], 0x02)
        self.assertEqual(parsed["sub"], 0x0A)
        self.assertEqual(len(parsed["payload"]), 7)

    def test_hryfine_worked_example_notification(self):
        # From PROTOCOL.md Example 3:
        # DF 00 11 A5 05 01 01 00 0C 01 05 41 6C 65 72 74 04 54 65 73 74
        frame = build_notification_alert(app_id=1, title="Alert", message="Test")
        self.assertEqual(frame.hex().upper(), "DF0011A5050101000C0105416C6572740454657374")
        parsed = parse_hryfine_frame(frame)
        self.assertEqual(parsed["cmd"], 0x05)
        self.assertEqual(parsed["sub"], 0x01)

    def test_hryfine_ack_roundtrip(self):
        ack = build_hryfine_ack(cmd=0x02, status=0x01)
        # Expected: FD 00 05 07 02 01 00 01 01
        self.assertEqual(ack.hex().upper(), "FD0005070201000101")
        parsed = parse_hryfine_frame(ack)
        self.assertEqual(parsed["type"], "ack")
        self.assertEqual(parsed["cmd"], 0x02)
        self.assertEqual(parsed["status"], 0x01)

    def test_hryfine_checksum_error(self):
        frame = bytearray(build_metadata_query())
        frame[3] ^= 0xFF  # corrupt checksum
        with self.assertRaises(ValueError) as ctx:
            parse_hryfine_frame(bytes(frame))
        self.assertIn("Checksum mismatch", str(ctx.exception))

    def test_hryfine_invalid_magic(self):
        frame = b"\xAA\x00\x05\x00\x00\x00\x00\x00\x00"
        with self.assertRaises(ValueError) as ctx:
            parse_hryfine_frame(frame)
        self.assertIn("Invalid magic", str(ctx.exception))

    def test_crc16_xmodem_vector(self):
        # Textbook check value for "123456789" is 0x31C3
        crc = crc16_xmodem(b"123456789")
        self.assertEqual(crc, 0x31C3)

    def test_jieli_worked_example_status_read(self):
        # From PROTOCOL.md Example 4:
        # FE DC BA C0 02 00 01 01 EF
        frame = build_jieli_frame(flag=0xC0, opcode=0x02, body=bytes([0x01]))
        self.assertEqual(frame.hex().upper(), "FEDCBAC002000101EF")
        parsed = parse_jieli_frame(frame)
        self.assertEqual(parsed["flag"], 0xC0)
        self.assertEqual(parsed["opcode"], 0x02)
        self.assertEqual(parsed["body"], bytes([0x01]))


if __name__ == "__main__":
    unittest.main()
