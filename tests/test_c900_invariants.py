"""Machine-checkable rows of targets/c900/INVARIANTS.md. Guards against quirks being dropped."""
import os, sys, unittest
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
from client.c900 import frames

INV = os.path.join(ROOT, "targets", "c900", "INVARIANTS.md")


class C900Invariants(unittest.TestCase):
    def test_blocklist_i20(self):
        self.assertEqual(frames.BLOCKED_CMDS, frozenset({0x01, 0x04, 0x06, 0x07, 0x0D, 0x13}))

    def test_vector_i11_i12(self):
        self.assertEqual(frames.build(frames.CMD_INFO, frames.SUB_INFO), bytes.fromhex("df0005ee0901000000"))

    def test_rows_present(self):
        with open(INV, encoding="utf-8") as f:
            text = f.read()
        for row in ["I-01", "I-10", "I-13", "I-20", "I-25", "I-30", "I-40", "I-41", "I-50", "I-53"]:
            self.assertIn("| " + row + " |", text, row)


if __name__ == "__main__":
    unittest.main()
