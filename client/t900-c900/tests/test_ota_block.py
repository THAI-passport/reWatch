"""OTA must be unreachable: by service id and, for JieLi, by RCSP opcode on 0xAE00."""
import asyncio
import os
import shutil
import tempfile
import unittest

from t900_c900.codecs import PROHIBITED_RCSP_OPCODES, build_jieli_frame, is_rcsp_ota_frame
from t900_c900.link import RecordingLink
from t900_c900.safe_write import SafeWriteGuard

AE01 = "0000ae01-0000-1000-8000-00805f9b34fb"


class OtaBlock(unittest.TestCase):
    def test_builder_refuses_ota_opcodes(self):
        self.assertIn(0xE5, PROHIBITED_RCSP_OPCODES)
        for op in (0xE0, 0xE5, 0xEF):
            with self.assertRaises(ValueError):
                build_jieli_frame(0xC0, op, b"\x01")
        build_jieli_frame(0xC0, 0x02, b"\x01")  # normal commands still build

    def test_link_refuses_hand_made_ota_frame_and_first_chunk(self):
        frame = b"\xfe\xdc\xba\xc0\xe5\x00\x01\x01\xef"
        self.assertTrue(is_rcsp_ota_frame(frame[:5]))
        link = RecordingLink(services=["ae00"])
        for data in (frame, frame[:5]):
            with self.assertRaises(RuntimeError):
                asyncio.run(link.write(AE01, data))
        self.assertEqual(link.writes, [])

    def test_link_allows_normal_rcsp(self):
        link = RecordingLink(services=["ae00"])
        asyncio.run(link.write(AE01, build_jieli_frame(0xC0, 0x02, b"\x01")))
        self.assertEqual(len(link.writes), 1)

    def test_unsourced_services_still_blocked(self):
        link = RecordingLink()
        for uuid in ("000018a8-0000-1000-8000-00805f9b34fb", "0000ae10-0000-1000-8000-00805f9b34fb"):
            with self.assertRaises(RuntimeError):
                asyncio.run(link.write(uuid, b"\x00"))


class GuardFailsClosed(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.g = SafeWriteGuard(state_dir=self.d, min_interval_seconds=0.0, daily_write_cap=3)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_corrupt_ledger_refuses_instead_of_resetting(self):
        addr = "AA:BB:CC:DD:EE:FF"
        for i in range(3):
            self.g.record_success(addr, b"p%d" % i)
        self.assertFalse(self.g.check_allowed(addr, b"new")[0])
        with open(self.g._state_file(addr), "w") as f:
            f.write("{truncated")
        allowed, msg = self.g.check_allowed(addr, b"new")
        self.assertFalse(allowed)
        self.assertIn("unreadable", msg)

    def test_save_is_atomic_no_tmp_left(self):
        self.g.record_success("AA", b"x")
        self.assertEqual([f for f in os.listdir(self.d) if f.endswith(".tmp")], [])


if __name__ == "__main__":
    unittest.main()
