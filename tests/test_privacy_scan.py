"""Tests for tools/privacy_scan.py (synthetic values only)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import privacy_scan as ps  # noqa: E402


def kinds(text, **kw):
    return [h["kind"] for h in ps.scan_text(text, **kw)]


class PrivacyScan(unittest.TestCase):
    def test_flags_identities(self):
        self.assertEqual(kinds("addr 5A:1B:2C:3D:4E:6F"), ["mac"])
        self.assertEqual(kinds("addr 5a:1b:2c:xx:xx:xx"), ["mac-oui-kept"])
        self.assertEqual(kinds("cb 1F2E3D4C-5B6A-7980-A1B2-C3D4E5F60718"), ["uuid"])
        self.assertEqual(kinds("imei 356938035643809"), ["imei"])
        self.assertIn("phone", kinds("call +66 81 234 5678"))
        self.assertEqual(kinds("mail someone@example.org"), ["email"])
        self.assertEqual(kinds("path /Users/alice/Desktop"), ["home-path"])

    def test_keeps_protocol_facts_and_masks(self):
        for ok in ("6e400002-b5a3-f393-e0a9-e50e24dcca9f", "00002a27-0000-1000-8000-00805f9b34fb",
                   "XX:XX:XX:XX:AB:CD", "xx:xx:xx:xx:xx:xx", "AA:BB:CC:DD:EE:01", "run 07:30:00-08:00:00",
                   "DF 00 05 ee 09 01 00 00 00", "hex=aacfe081dff6fc3800000000000010e64108cf14",
                   "/home/user/reWatch", "7905F431-B5CE-4E99-A40F-4B1E122D00D0"):
            self.assertEqual(kinds(ok), [], ok)

    def test_strict_flags_spaced_bytes(self):
        self.assertEqual(kinds("41 42 d0 13 d7 cc"), [])
        self.assertEqual(kinds("41 42 d0 13 d7 cc", strict=True), ["mac-hex-run"])

    def test_never_echoes_full_value(self):
        h = ps.scan_text("5A:1B:2C:3D:4E:6F")[0]
        self.assertNotIn("4E:6F", h["match"])

    def test_allow(self):
        self.assertEqual(kinds("5A:1B:2C:3D:4E:6F", allow=[r"^5A:1B"]), [])

    def test_repo_docs_are_clean(self):
        paths = [os.path.join(ROOT, p) for p in ("targets", "docs", ".claude", "FIXES.md", "AGENTS.md")]
        self.assertEqual(ps.main(paths + ["--json"]), 0)


if __name__ == "__main__":
    unittest.main()
