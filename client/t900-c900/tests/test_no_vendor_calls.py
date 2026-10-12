"""Test verifying that client codebase makes zero vendor or analytics calls."""
import os
import re
import unittest

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PACKAGE_DIR, "t900_c900")

SUSPICIOUS_NET_PATTERNS = [
    re.compile(r"https?://(?!example\.com|127\.0\.0\.1|localhost)", re.IGNORECASE),
    re.compile(r"\burllib\.request\b"),
    re.compile(r"\brequests\.(?:get|post|put|delete)\b"),
    re.compile(r"\baiohttp\b"),
    re.compile(r"\bumeng\b", re.IGNORECASE),
    re.compile(r"\bappsflyer\b", re.IGNORECASE),
    re.compile(r"\badjust\.com\b", re.IGNORECASE),
]


class TestNoVendorCalls(unittest.TestCase):
    def test_client_contains_no_vendor_or_network_calls(self):
        for root, _, files in os.walk(SRC_DIR):
            for file in files:
                if not file.endswith(".py"):
                    continue
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                for pat in SUSPICIOUS_NET_PATTERNS:
                    m = pat.search(content)
                    self.assertIsNone(
                        m,
                        f"Found unauthorized network or tracking pattern '{pat.pattern}' in {file}: {m.group(0) if m else ''}",
                    )


if __name__ == "__main__":
    unittest.main()
