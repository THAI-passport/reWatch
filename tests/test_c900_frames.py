import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client.c900 import frames


class C900Frames(unittest.TestCase):
    # Built-ahead consistency tests: they check the codec against itself and the [W] layout,
    # not against the real app or watch.
    def test_build_layout(self):
        f = frames.build(frames.CMD_TIME, frames.SUB_TIME, b"\x01\x02")
        self.assertEqual(f[0], 0xDF)
        self.assertEqual(f[4:7], bytes([0x02, 0x01, 0x01]))
        self.assertEqual(int.from_bytes(f[1:3], "big") + 4, len(f))
        self.assertEqual(f[7:9], b"\x00\x02")

    def test_checksum_vector(self):
        f = frames.build(frames.CMD_INFO, frames.SUB_INFO)
        self.assertEqual(f, bytes.fromhex("df0005ee0901000000"))

    def test_roundtrip_and_ack(self):
        sim = frames.SimWatch()
        a = sim.write(frames.build(frames.CMD_TIME, frames.SUB_TIME, b"abc"))
        self.assertEqual(sim.received, [(0x02, 0x01, b"abc")])
        self.assertEqual(frames.parse(a)[:2], (0xFD, 0x02))

    def test_rejects_bad_checksum(self):
        f = bytearray(frames.build(0x02, 0x0A, b"x"))
        f[-1] ^= 1
        with self.assertRaises(ValueError):
            frames.parse(bytes(f))

    def test_ver_parameter(self):
        self.assertEqual(frames.build(0x09, 0x00), frames.build(0x09, 0x00, ver=frames.DEFAULT_VER))
        f = frames.build(0x02, 0x0B, b"\x01", ver=frames.C900_VER)
        self.assertEqual(f[5], 0x10)
        self.assertEqual(frames.parse(f), (0xDF, 0x02, 0x0B, b"\x01"))
        with self.assertRaises(ValueError):
            frames.build(0x02, 0x0B, b"", ver=256)
        with self.assertRaises(frames.BlockedCommand):
            frames.build(0x04, 0x00, ver=0x10)

    def test_c900_capture_vector(self):
        """Time sync as seen in C900-Q19: ver 0x10, payload 6a9b05cb = 2026-10-13 16:23:11 [H]."""
        f = frames.build(0x02, 0x01, frames.time_payload(2026, 10, 13, 16, 23, 11), ver=frames.C900_VER)
        self.assertEqual(f[:3], bytes.fromhex("df0009"))  # I-11; Q19 excerpt "00 08" was a hand-copy typo (ack x = 13 implies len 9)
        self.assertEqual(f[4:], bytes.fromhex("02100100046a9b05cb"))

    def test_ver_from_hw_revision(self):
        self.assertEqual(frames.ver_from_hw_revision(b"10000"), 0x10)
        self.assertEqual(frames.ver_from_hw_revision(b"V1.2"), 0x01)
        self.assertIsNone(frames.ver_from_hw_revision(b""))
        self.assertIsNone(frames.ver_from_hw_revision(b"HW-A"))

    def test_simwatch_ack_is_frame_length(self):
        sim = frames.SimWatch(ver=frames.C900_VER)
        f = frames.build(0x02, 0x01, b"\x00" * 4, ver=frames.C900_VER)
        a = sim.write(f)
        self.assertEqual((a[4], a[5], (a[6] << 8) | a[7], a[8]), (0x02, 0x01, 13, 1))  # 4 + 9 [H]
        self.assertEqual(sim.vers, [0x10])


if __name__ == "__main__":
    unittest.main()


class C900AgainstHiwearPlus(unittest.TestCase):
    # Layout rules read from Hiwear Plus 2.0.1 (targets/c900/PROTOCOL.md section 4) [C]; vector is own arithmetic.
    def test_settings_query_vector(self):
        self.assertEqual(frames.build(0x09, 0x00), bytes.fromhex("df0005ee0901000000"))

    def test_len_counts_cmd_to_payload(self):
        f = frames.build(0x02, 0x12, b"\x01\x00\x00hi")
        self.assertEqual(int.from_bytes(f[1:3], "big"), 5 + 5)



class C900Safety(unittest.TestCase):
    def test_blocklist_refuses_every_dangerous_id(self):
        for c in (0x01, 0x04, 0x06, 0x07, 0x0D, 0x13):
            with self.assertRaises(frames.BlockedCommand):
                frames.build(c, 0x00)

    def test_allowed_ids_still_build(self):
        for c in (0x02, 0x03, 0x09, 0x0F):
            frames.build(c, 0x00)

    def test_time_payload_packing(self):
        # own arithmetic from the smali formula: 2026-10-13 14:05:30
        # b0=(26<<2)|(10>>2)=0x6A b1=(2<<6)|(13<<1)|(14>>4)=0x9A b2=(14<<4)|(5>>2)=0xE1 b3=(1<<6)|30=0x5E
        self.assertEqual(frames.time_payload(2026, 10, 13, 14, 5, 30), bytes.fromhex("6a9ae15e"))
        f = frames.build(frames.CMD_SETTING, frames.KEY_TIME, frames.time_payload(2026, 10, 13, 14, 5, 30))
        self.assertEqual(f[:3], bytes.fromhex("df0009"))
        self.assertEqual(frames.parse(f)[1:], (0x02, 0x01, bytes.fromhex("6a9ae15e")))
        with self.assertRaises(ValueError):
            frames.time_payload(1999, 1, 1, 0, 0, 0)
