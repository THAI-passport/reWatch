import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client.c900 import frames


class C900Frames(unittest.TestCase):
    # Built-ahead consistency tests: they check the codec against itself and the [W] layout,
    # not against the real app or watch.
    def test_build_layout(self):
        f = frames.build(frames.CMD_TIME, frames.SUB_TIME, b"\x01\x02")
        self.assertEqual(f[0], 0xDF)
        self.assertEqual(f[4:7], bytes([0x02, 0x01, 0x0A]))
        self.assertEqual(int.from_bytes(f[1:3], "big") + 4, len(f))
        self.assertEqual(f[7:9], b"\x00\x02")

    def test_checksum_vector(self):
        # hand check: 0xDF + 0x05 + 0xF3 + 0x01 = 0x1D8, low byte 0xD8 (own arithmetic, [W] rule)
        f = frames.build(frames.CMD_INFO, frames.SUB_INFO)
        self.assertEqual(f, bytes.fromhex("df0005d8f3010000 00".replace(" ", "")))

    def test_roundtrip_and_ack(self):
        sim = frames.SimWatch()
        a = sim.write(frames.build(frames.CMD_TIME, frames.SUB_TIME, b"abc"))
        self.assertEqual(sim.received, [(0x02, 0x0A, b"abc")])
        self.assertEqual(frames.parse(a)[:2], (0xFD, 0x02))

    def test_rejects_bad_checksum(self):
        f = bytearray(frames.build(0x02, 0x0A, b"x"))
        f[-1] ^= 1
        with self.assertRaises(ValueError):
            frames.parse(bytes(f))


if __name__ == "__main__":
    unittest.main()


class C900AgainstHiwearPlus(unittest.TestCase):
    # Layout rules read from Hiwear Plus 2.0.1 (targets/c900/PROTOCOL.md section 4) [C]; vector is own arithmetic.
    def test_settings_query_vector(self):
        self.assertEqual(frames.build(0x09, 0x00), bytes.fromhex("df0005ee0901000000"))

    def test_len_counts_cmd_to_payload(self):
        f = frames.build(0x02, 0x12, b"\x01\x00\x00hi")
        self.assertEqual(int.from_bytes(f[1:3], "big"), 5 + 5)

