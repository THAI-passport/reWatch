"""Unit tests for safe-write flash protection guard."""
import shutil
import tempfile
import unittest
from t900_c900.safe_write import SafeWriteGuard


class TestSafeWrite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.guard = SafeWriteGuard(
            state_dir=self.temp_dir,
            min_interval_seconds=0.0,
            daily_write_cap=3,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_first_write_permitted(self):
        allowed, msg = self.guard.check_allowed("AA:BB:CC:DD:EE:FF", b"test_payload")
        self.assertTrue(allowed)
        self.guard.record_success("AA:BB:CC:DD:EE:FF", b"test_payload")

    def test_delta_skip_identical_payload(self):
        self.guard.record_success("AA:BB:CC:DD:EE:FF", b"identical_payload")
        allowed, msg = self.guard.check_allowed("AA:BB:CC:DD:EE:FF", b"identical_payload")
        self.assertFalse(allowed)
        self.assertIn("Delta skip", msg)

        # Allow identical flag should bypass delta skip
        allowed_bypass, _ = self.guard.check_allowed(
            "AA:BB:CC:DD:EE:FF", b"identical_payload", allow_identical=True
        )
        self.assertTrue(allowed_bypass)

    def test_daily_cap_enforcement(self):
        addr = "AA:BB:CC:DD:EE:01"
        for i in range(3):
            allowed, _ = self.guard.check_allowed(addr, f"payload_{i}".encode())
            self.assertTrue(allowed)
            self.guard.record_success(addr, f"payload_{i}".encode())

        # 4th write should be blocked by daily cap
        allowed, msg = self.guard.check_allowed(addr, b"payload_4")
        self.assertFalse(allowed)
        self.assertIn("Daily flash write cap", msg)

    def test_dry_run_does_not_mutate_state(self):
        addr = "AA:BB:CC:DD:EE:02"
        allowed, _ = self.guard.check_allowed(addr, b"dry_payload", dry_run=True)
        self.assertTrue(allowed)
        self.guard.record_success(addr, b"dry_payload", dry_run=True)

        state = self.guard._load_state(addr)
        self.assertEqual(state["daily_count"], 0)

    def test_rate_limit_interval(self):
        guard = SafeWriteGuard(state_dir=self.temp_dir, min_interval_seconds=10.0)
        guard.record_success("AA:BB:CC:DD:EE:03", b"msg1")
        allowed, msg = guard.check_allowed("AA:BB:CC:DD:EE:03", b"msg2")
        self.assertFalse(allowed)
        self.assertIn("minimum write interval", msg)


if __name__ == "__main__":
    unittest.main()
