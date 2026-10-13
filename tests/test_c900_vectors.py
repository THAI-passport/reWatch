"""The shared vector file must match the Python reference codec (the Kotlin core reads it)."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from client.c900 import vectors  # noqa: E402


class Vectors(unittest.TestCase):
    def test_fixture_is_current(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "c900_vectors.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), vectors.build_vectors(),
                             "regenerate: python -m client.c900.vectors > tests/fixtures/c900_vectors.json")

    def test_capture_vector_present(self):
        names = {v["name"]: v for v in vectors.build_vectors()["frames"]}
        self.assertEqual(names["find_on_c900"]["frame"], "df00060402100b000101")   # the frame this codec built for LIVE-SESSION-2 (ack x=10 matched)


if __name__ == "__main__":
    unittest.main()
