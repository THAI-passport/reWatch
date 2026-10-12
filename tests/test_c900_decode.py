"""tools/c900_decode.py on the synthetic C900 capture (tests/fixtures/c900_synthetic.btsnoop). Decode only."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures"))
import btcap  # noqa: E402
import c900_decode as dec  # noqa: E402
import make_c900_fixture  # noqa: E402
from client.c900 import frames  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures", "c900_synthetic.btsnoop")


class Decode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames, cls.reads, cls.s = dec.decode(dec.rows_from_capture(FIX))

    def test_fixture_is_reproducible(self):
        self.assertEqual(open(FIX, "rb").read(), make_c900_fixture.build())

    def test_each_frame_decoded(self):
        got = [(f["dir"], f["type"], f["cmd"], f["key"]) for f in self.frames]
        self.assertEqual(got, [("tx", "cmd", 3, 0), ("rx", "ack", 3, 0), ("tx", "cmd", 2, 1), ("rx", "ack", 2, 1), ("tx", "cmd", 2, 18),
                               ("rx", "cmd", 5, 14), ("rx", "cmd", 12, 2), ("rx", "cmd", 12, 19), ("rx", "cmd", 14, 1),
                               ("rx", "cmd", 12, 1), ("tx", "cmd", 4, 0)])

    def test_reassembly_across_writes_and_notifies(self):
        msg = [f for f in self.frames if f["cmd"] == 2 and f["key"] == 18][0]
        spo2 = [f for f in self.frames if f["cmd"] == 5][0]
        self.assertTrue(msg["sum_ok"] and msg["plen_ok"] and spo2["sum_ok"])
        self.assertEqual(spo2["payload"][-2:], "61")
        self.assertIn("SpO2", spo2["label"])

    def test_privacy_text_hidden_and_mac_masked(self):
        out = dec.render(self.frames, self.reads, self.s)
        self.assertNotIn("synthetic:test", out)
        self.assertNotIn(b"synthetic:test".hex(), out)
        self.assertIn("xx:xx:xx:xx:00:01", out)
        self.assertNotIn("020000000001", out)

    def test_summary_block(self):
        s = self.s
        self.assertEqual(s["versions_seen"], [1])
        self.assertEqual((s["hw_version"], s["fw_version"], s["battery"]), ("V1.2", "SYN-0.0.1", 77))
        self.assertTrue(s["features"]["marker_ok"])
        self.assertEqual(len(s["bond_triggers"]), 3)
        self.assertEqual(s["blocked_cmds"], ["0x04 UNBIND"])
        self.assertEqual(s["bad_sum"], 1)
        self.assertEqual(len(s["ota_traffic"]), 1)
        out = dec.render(self.frames, self.reads, self.s)
        for line in ("bond triggers seen: yes", "blocked cmds seen: YES", "OTA/DFU traffic seen: YES", "version byte(s) seen in app frames: [1]"):
            self.assertIn(line, out)

    def test_matches_client_codec(self):
        f = frames.build(frames.CMD_INFO, frames.SUB_INFO)
        d = dec.decode_frame(f, "tx")
        self.assertTrue(d["sum_ok"])
        self.assertEqual((d["cmd"], d["key"], d["ver"]), (9, 0, 1))
        a = dec.decode_frame(frames.ack(3), "rx")
        self.assertEqual((a["type"], a["cmd"], a["status"], a["sum_ok"]), ("ack", 3, 1, True))

    def test_json_input_path_and_cli(self):
        tmp = tempfile.mkdtemp()
        j = os.path.join(tmp, "rows.json")
        with redirect_stdout(io.StringIO()):
            btcap.main([FIX, "--json", j])
            buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(dec.main([j, "--json", os.path.join(tmp, "o.json")]), 0)
        self.assertIn("SUMMARY", buf.getvalue())
        self.assertEqual(json.load(open(os.path.join(tmp, "o.json")))["summary"]["frames_rx"], 7)

    def test_stray_chunk_counted(self):
        r = dec.Reassembler()
        self.assertEqual(r.feed(b"\x00\x01"), [])
        self.assertEqual(r.stray, 1)

    def test_decode_only_no_radio_code(self):
        src = open(os.path.join(ROOT, "tools", "c900_decode.py")).read()
        for word in ("bleak", "write_gatt", "socket", "start_notify", "subprocess"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main()
