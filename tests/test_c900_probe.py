"""Safety and correctness tests for tools/c900_probe.py. No real radio."""
from __future__ import annotations

import ast
import asyncio
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import c900_probe as probe  # noqa: E402
from client.c900 import frames  # noqa: E402


# ---------------------------------------------------------------------------
# Fake bleak
# ---------------------------------------------------------------------------
class FakeAdv:
    def __init__(self, name, rssi=-50, mfg=None):
        self.local_name, self.rssi, self.manufacturer_data = name, rssi, mfg or {}


class FakeDev:
    def __init__(self, name):
        self.name = name


class FakeChar:
    def __init__(self, uuid, properties):
        self.uuid, self.properties = uuid, properties


class FakeSvc:
    def __init__(self, uuid, chars):
        self.uuid, self.characteristics = uuid, chars


def _u(spec):
    return str(getattr(spec, "uuid", spec)).lower()


class FakeClient:
    """Simulated C900. Configurable for abort / layout / ack scenarios."""
    instances = []

    def __init__(self, address, timeout=20.0):
        self.address = address
        self.timeout = timeout
        self.is_connected = False
        self.is_paired = False
        self.handlers = {}
        self.writes = []
        self.write_responses = []
        self.reads = {}
        self.services = self._default_services()
        self.pair_calls = 0
        self._auto_ack = True
        self._inbound_after_write = None
        self._flip_paired = False
        FakeClient.instances.append(self)

    def _default_services(self):
        n = lambda u, *p: FakeChar(u, list(p))  # noqa: E731
        return [
            FakeSvc("6e400001-b5a3-f393-e0a9-e50e24dcca9f", [
                n(probe.WRITE_UUID, "write-without-response"),
                n(probe.NOTIFY_UUID, "notify"),
            ]),
            FakeSvc("0000ff00-0000-1000-8000-00805f9b34fb", [
                n("0000ff01-0000-1000-8000-00805f9b34fb", "notify"),
                n("0000ff02-0000-1000-8000-00805f9b34fb", "write-without-response"),
            ]),
            FakeSvc("000018a8-0000-1000-8000-00805f9b34fb", [
                n("00002aa8-0000-1000-8000-00805f9b34fb", "notify"),
            ]),
            FakeSvc("6e40ff01-b5a3-f393-e0a9-e50e24dcca9e", [
                n("6e40ff03-b5a3-f393-e0a9-e50e24dcca9e", "notify"),
            ]),
            FakeSvc("0000180a-0000-1000-8000-00805f9b34fb", [
                n("00002a26-0000-1000-8000-00805f9b34fb", "read"),
                n("00002a27-0000-1000-8000-00805f9b34fb", "read"),
                n("00002a28-0000-1000-8000-00805f9b34fb", "read"),
            ]),
            FakeSvc("0000180f-0000-1000-8000-00805f9b34fb", [
                n("00002a19-0000-1000-8000-00805f9b34fb", "read"),
            ]),
        ]

    async def connect(self):
        self.is_connected = True
        if self._flip_paired:
            self.is_paired = True

    async def disconnect(self):
        self.is_connected = False

    async def pair(self):
        self.pair_calls += 1
        self.is_paired = True

    async def start_notify(self, uuid, cb):
        u = _u(uuid)
        if probe.is_ota_uuid(u):
            raise AssertionError("test guard: start_notify on OTA uuid %s" % u)
        self.handlers[u] = cb

    async def stop_notify(self, uuid):
        self.handlers.pop(_u(uuid), None)

    async def read_gatt_char(self, uuid):
        u = _u(uuid)
        if u in self.reads:
            return self.reads[u]
        if len(u) == 36 and u.startswith("0000"):
            u = u[4:8]  # the probe reads by full base UUID; the old fake only matched short forms
        if u.endswith("2a19"):
            return bytes([77])
        if u.endswith("2a27"):
            return b"V1.2"
        if u.endswith("2a26"):
            return b"SYN-0.0.1"
        if u.endswith("2a28"):
            b = bytearray(26); b[0], b[1], b[15], b[25] = 0xAA, 0x00, 0x00, 0x00
            return bytes(b)
        return self.reads.get(u, b"")

    async def write_gatt_char(self, uuid, data, response=False):
        if not isinstance(uuid, FakeChar):
            raise AssertionError("test guard: write by bare UUID, not the command characteristic object")
        self.write_responses.append(response)
        u = _u(uuid)
        if probe.is_ota_uuid(u):
            raise AssertionError("test guard: write to OTA uuid %s" % u)
        if u != probe.WRITE_UUID:
            raise AssertionError("test guard: write to non-command uuid %s" % u)
        self.writes.append(bytes(data))
        if self._auto_ack and self.handlers.get(probe.NOTIFY_UUID):
            # Parse assembled pieces if this was the last piece of a DF frame.
            blob = b"".join(self.writes)
            if len(blob) >= 9 and blob[0] == 0xDF:
                total = ((blob[1] << 8) | blob[2]) + 4
                if len(blob) >= total:
                    cmd, key = blob[4], blob[6]
                    self.handlers[probe.NOTIFY_UUID](None, frames.ack(cmd, key))
                    self.writes.clear()
        if self._inbound_after_write and self.handlers.get(probe.NOTIFY_UUID):
            self.handlers[probe.NOTIFY_UUID](None, self._inbound_after_write)
            self._inbound_after_write = None


class FakeScanner:
    devices = {"AA:BB:CC:DD:EE:01": (FakeDev("C900-Test"), FakeAdv("C900-Test", -60, {0x0102: bytes.fromhex("aabbccddeeff1234")})),
               "AA:BB:CC:DD:EE:02": (FakeDev("Other"), FakeAdv("Other", -70))}

    @staticmethod
    async def discover(timeout=5.0, return_adv=True):
        return dict(FakeScanner.devices)


class FakeBleak:
    BleakClient = FakeClient
    BleakScanner = FakeScanner


def install_fake():
    FakeClient.instances.clear()
    probe._bleak_mod = FakeBleak


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class Sanitize(unittest.TestCase):
    def test_strips_controls_and_caps(self):
        self.assertEqual(probe.sanitize("a\x00b\nc"), "a?b c")
        self.assertTrue(probe.sanitize("x" * 200).endswith("..."))
        self.assertNotIn("%", probe.sanitize("x%s"))
        self.assertNotIn("../", probe.sanitize("../etc/passwd"))

    def test_mask_and_redact(self):
        self.assertEqual(probe.mask_mac("AA:BB:CC:DD:EE:FF"), "AA:BB:CC:xx:xx:xx")
        self.assertIn("xx:xx:xx", probe.redact_line("saw AA:BB:CC:DD:EE:FF"))
        self.assertIn("<redacted>", probe.redact_line("message push payload=secret"))
        redacted_caller = probe.redact_line("caller id from +123456789")
        self.assertIn("<redacted>", redacted_caller)
        self.assertNotIn("+123456789", redacted_caller)


class Allowlist(unittest.TestCase):
    def test_builds_only_allowlisted(self):
        for name in ("time", "message", "find"):
            cmd, key, f = probe.build_allowlisted(name)
            self.assertIn((cmd, key), probe.ALLOWLIST)
            self.assertNotIn(cmd, frames.BLOCKED_CMDS)
            self.assertEqual(f[0], 0xDF)
            self.assertEqual(frames.checksum(f), f[3])

    def test_message_text_is_fixed(self):
        _, _, f = probe.build_allowlisted("message")
        self.assertIn(b"reWatch test", f)
        self.assertEqual(f[9], 1)  # type SMS

    def test_unknown_and_blocked_refused(self):
        with self.assertRaises(probe.SafetyError):
            probe.build_allowlisted("unbind")
        with self.assertRaises(probe.SafetyError):
            probe.build_allowlisted("ota")
        # Even a direct frames.build of a blocked cmd is refused by frames.
        with self.assertRaises(frames.BlockedCommand):
            frames.build(0x04, 0)


class OtaRefusal(unittest.TestCase):
    def test_is_ota_uuid(self):
        for u in ("ff00", "0000ff02-0000-1000-8000-00805f9b34fb", "18a8",
                  "6e40ff01-b5a3-f393-e0a9-e50e24dcca9e", "6e40ff03-b5a3-f393-e0a9-e50e24dcca9e", "5610",
                  "12345610-1111-2222-3333-444455556666"):
            self.assertTrue(probe.is_ota_uuid(u), u)
        self.assertFalse(probe.is_ota_uuid(probe.WRITE_UUID))
        self.assertFalse(probe.is_ota_uuid(probe.NOTIFY_UUID))

    def test_command_uuids_not_ota_despite_5610_rule(self):
        """Regression: '5610' substring rule must not classify the DF service as OTA."""
        for u in (probe.WRITE_UUID, probe.NOTIFY_UUID,
                  "6e400001-b5a3-f393-e0a9-e50e24dcca9f",
                  "00002a19-0000-1000-8000-00805f9b34fb",
                  "0000180a-0000-1000-8000-00805f9b34fb"):
            self.assertNotIn("5610", u)
            self.assertFalse(probe.is_ota_uuid(u), u)

    def test_layout_requires_command_service(self):
        bad = [FakeSvc("0000180f-0000-1000-8000-00805f9b34fb",
                       [FakeChar("00002a19-0000-1000-8000-00805f9b34fb", ["read"])])]
        with self.assertRaises(probe.SafetyError):
            probe._require_command_layout(bad)

    def test_ota_lookalike_write_refused(self):
        n = lambda u, *p: FakeChar(u, list(p))  # noqa: E731
        bad = [
            FakeSvc("6e400001-b5a3-f393-e0a9-e50e24dcca9f", [
                n(probe.WRITE_UUID, "write"),
                n(probe.NOTIFY_UUID, "notify"),
            ]),
            FakeSvc("6e40ff01-b5a3-f393-e0a9-e50e24dcca9e", [
                n("6e400002-b5a3-f393-e0a9-e50e24dcca9e", "write"),
            ]),
        ]
        with self.assertRaises(probe.SafetyError):
            probe._require_command_layout(bad)

    def test_write_uuid_under_ota_svc_refused(self):
        n = lambda u, *p: FakeChar(u, list(p))  # noqa: E731
        bad = [
            FakeSvc("0000ff00-0000-1000-8000-00805f9b34fb", [
                n(probe.WRITE_UUID, "write"),
                n(probe.NOTIFY_UUID, "notify"),
            ]),
        ]
        with self.assertRaises(probe.SafetyError):
            probe._require_command_layout(bad)


class TargetRequired(unittest.TestCase):
    def setUp(self):
        install_fake()

    def test_inspect_without_target_fails(self):
        rc = probe.main(["inspect", "--listen", "0.01", "--log-dir", tempfile.mkdtemp()], confirm_fn=lambda p: "")
        self.assertEqual(rc, probe.EXIT_SAFETY)

    def test_name_must_be_exact_and_unique(self):
        rc = probe.main(["inspect", "--name", "nope", "--listen", "0.01", "--log-dir", tempfile.mkdtemp()],
                        confirm_fn=lambda p: "")
        self.assertEqual(rc, probe.EXIT_SAFETY)

    def test_address_and_name_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            probe.build_parser().parse_args(["inspect", "--address", "AA:BB:CC:DD:EE:01", "--name", "Test"])


class InspectSafe(unittest.TestCase):
    def setUp(self):
        install_fake()
        self.logdir = tempfile.mkdtemp()

    def test_inspect_listens_only_command_notify(self):
        rc = probe.main(["inspect", "--address", "AA:BB:CC:DD:EE:01", "--listen", "0.05", "--log-dir", self.logdir],
                        confirm_fn=lambda p: "")
        self.assertEqual(rc, 0)
        c = FakeClient.instances[-1]
        self.assertEqual(list(c.handlers), [])  # stopped
        self.assertEqual(c.pair_calls, 0)
        self.assertEqual(c.writes, [])  # no DF writes in inspect
        # log exists and masks MAC
        logs = [f for f in os.listdir(self.logdir) if f.endswith(".log")]
        self.assertEqual(len(logs), 1)
        text = open(os.path.join(self.logdir, logs[0])).read()
        self.assertNotIn("AA:BB:CC:DD:EE:01", text)
        self.assertIn("xx:xx:xx", text)
        self.assertIn("LAYOUT ok", text)


class BondTriggerAbort(unittest.TestCase):
    def setUp(self):
        install_fake()
        self.logdir = tempfile.mkdtemp()

    def test_inbound_bond_trigger_aborts_safe_write(self):
        # Inject a bond-trigger frame when the write happens.
        original_init = FakeClient.__init__

        def init(self, *a, **k):
            original_init(self, *a, **k)
            # 0x0C key 19 DF frame
            body = bytes([0x0C, 0x01, 19]) + (0).to_bytes(2, "big")
            n = len(body)
            f = bytearray([0xDF, n >> 8, n & 0xFF, 0]) + body
            f[3] = frames.checksum(f)
            self._inbound_after_write = bytes(f)
            self._auto_ack = False

        FakeClient.__init__ = init
        try:
            rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                             "--i-approve-writes", "--log-dir", self.logdir],
                            confirm_fn=lambda p: "find")
        finally:
            FakeClient.__init__ = original_init
        self.assertEqual(rc, probe.EXIT_SAFETY)

    def test_leading_garbage_resyncs_and_aborts_on_bond_trigger(self):
        original_init = FakeClient.__init__

        def init(self, *a, **k):
            original_init(self, *a, **k)
            # Leading noise byte \x00 followed by 0x0C key 19 frame
            body = bytes([0x0C, 0x01, 19]) + (0).to_bytes(2, "big")
            n = len(body)
            f = bytearray([0xDF, n >> 8, n & 0xFF, 0]) + body
            f[3] = frames.checksum(f)
            self._inbound_after_write = b"\x00" + bytes(f)
            self._auto_ack = False

        FakeClient.__init__ = init
        try:
            rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                             "--i-approve-writes", "--log-dir", self.logdir],
                            confirm_fn=lambda p: "find")
        finally:
            FakeClient.__init__ = original_init
        self.assertEqual(rc, probe.EXIT_SAFETY)


class PairingAbort(unittest.TestCase):
    def setUp(self):
        install_fake()

    def test_pairing_flip_aborts_inspect(self):
        original = FakeClient.connect

        async def connect(self):
            self.is_connected = True
            self.is_paired = True  # flipped on connect

        FakeClient.connect = connect
        try:
            pass
        finally:
            FakeClient.connect = original

        # Drive flip during listen via a custom client.
        class FlipClient(FakeClient):
            async def connect(self):
                self.is_connected = True
                self.is_paired = False

            async def start_notify(self, uuid, cb):
                await super().start_notify(uuid, cb)
                self.is_paired = True  # stack starts pairing

        FakeBleak.BleakClient = FlipClient
        try:
            rc = probe.main(["inspect", "--address", "AA:BB:CC:DD:EE:01", "--listen", "0.3",
                             "--log-dir", tempfile.mkdtemp()], confirm_fn=lambda p: "")
        finally:
            FakeBleak.BleakClient = FakeClient
        self.assertEqual(rc, probe.EXIT_SAFETY)

    def test_pairing_flip_aborts_safe_write(self):
        class FlipClient(FakeClient):
            async def connect(self):
                self.is_connected = True
                self.is_paired = False

            async def write_gatt_char(self, uuid, data, response=False):
                await super().write_gatt_char(uuid, data, response=response)
                self.is_paired = True  # stack starts pairing upon write

        FakeBleak.BleakClient = FlipClient
        try:
            rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                             "--i-approve-writes", "--log-dir", tempfile.mkdtemp()],
                            confirm_fn=lambda p: "find")
        finally:
            FakeBleak.BleakClient = FakeClient
        self.assertEqual(rc, probe.EXIT_SAFETY)


class WriteCapAndApproval(unittest.TestCase):
    def setUp(self):
        install_fake()
        self.logdir = tempfile.mkdtemp()

    def test_requires_approve_flag_and_typed_confirm(self):
        rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                         "--log-dir", self.logdir], confirm_fn=lambda p: "find")
        self.assertEqual(rc, probe.EXIT_SAFETY)
        rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                         "--i-approve-writes", "--log-dir", self.logdir], confirm_fn=lambda p: "nope")
        self.assertEqual(rc, probe.EXIT_SAFETY)
        self.assertTrue(not FakeClient.instances or FakeClient.instances[-1].writes == [])

    def test_happy_path_find(self):
        rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                         "--i-approve-writes", "--log-dir", self.logdir], confirm_fn=lambda p: "find")
        self.assertEqual(rc, 0)
        c = FakeClient.instances[-1]
        self.assertEqual(c.pair_calls, 0)
        blob = b"".join(c.writes) if c.writes else b""
        # after auto-ack the buffer is cleared; check it was a find frame via log
        text = open(os.path.join(self.logdir, os.listdir(self.logdir)[0])).read()
        self.assertIn("ACK ok", text)
        self.assertIn("command=find", text)

    def test_write_cap_pre_check_refuses_atomically(self):
        original_amain = probe.mode_safe_write

        async def wrapped(address, command, log, budget, approve, confirm_fn, name_filter=None):
            budget.writes = probe.MAX_WRITES  # budget exhausted before write
            return await original_amain(address, command, log, budget, approve, confirm_fn, name_filter)

        probe.mode_safe_write = wrapped
        try:
            rc = probe.main(["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                             "--i-approve-writes", "--log-dir", self.logdir], confirm_fn=lambda p: "find")
        finally:
            probe.mode_safe_write = original_amain
        self.assertEqual(rc, probe.EXIT_SAFETY)
        self.assertTrue(not FakeClient.instances or FakeClient.instances[-1].writes == [])

    def test_write_cap(self):
        b = probe.Budget()
        for _ in range(probe.MAX_WRITES):
            b.charge_write()
        with self.assertRaises(probe.SafetyError):
            b.charge_write()


class ResyncAndRedaction(unittest.TestCase):
    def test_resync_preserves_real_frames(self):
        """Leading noise then a split ack must parse the ack (not skip a real frame)."""
        buf = bytearray()

        def feed(data):
            buf.extend(data)
            out = []
            while buf:
                while buf and buf[0] not in (0xDF, 0xFD):
                    del buf[0]
                if len(buf) < 3:
                    break
                total = ((buf[1] << 8) | buf[2]) + 4
                if total < 9 or total > 1024:
                    del buf[0]
                    continue
                if len(buf) < total:
                    break
                out.append(probe.parse_inbound(bytes(buf[:total])))
                del buf[:total]
            return out

        ack = frames.ack(0x02, 0x0B)
        self.assertEqual(feed(b"\x00\xff" + ack[:4]), [])
        got = feed(ack[4:])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["kind"], "ack")
        self.assertEqual((got[0]["cmd"], got[0]["key"], got[0]["status"]), (0x02, 0x0B, 1))
        # second real frame after more noise
        ack2 = frames.ack(0x02, 0x01)
        got2 = feed(b"\x11\x22" + ack2)
        self.assertEqual(got2[0]["key"], 0x01)

    def test_redaction_keeps_protocol_fields(self):
        for line in ("RX cmd=0x0c key=2 plen=0",
                     "READ features marker=0xaa len=26 bits=(isBLE3: False)",
                     "ACK ok cmd=0x02 key=0x0b status=1",
                     "TX piece 1/1 len=10"):
            self.assertEqual(probe.redact_line(line), line)

    def test_write_cap_math_multi_piece(self):
        _, _, frame = probe.build_allowlisted("message")
        pieces = [frame[i:i + 20] for i in range(0, len(frame), 20)]
        self.assertGreaterEqual(len(pieces), 2)
        used = probe.MAX_WRITES - len(pieces) + 1
        self.assertTrue(used + len(pieces) > probe.MAX_WRITES)


class ForbiddenImports(unittest.TestCase):
    def test_ast_scan(self):
        src = open(os.path.join(ROOT, "tools", "c900_probe.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        banned = {"eval", "exec", "compile", "__import__"}
        banned_mod = {"subprocess", "socket", "requests", "pickle", "pathlib", "http", "urllib",
                      "importlib", "ctypes", "multiprocessing"}
        # pathlib is imported at top for Path - wait, we DO import pathlib. That's fine for Path.
        # Re-scope: banned runtime modules that imply network/code-exec.
        banned_mod = {"subprocess", "socket", "requests", "pickle", "http", "urllib",
                      "importlib", "ctypes", "multiprocessing", "pty", "commands"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in banned:
                self.fail("banned call %s" % node.func.id)
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn(a.name.split(".")[0], banned_mod, a.name)
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn(node.module.split(".")[0], banned_mod, node.module)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "os" and node.attr in ("system", "popen", "exec", "execl", "execv", "spawnl"):
                    self.fail("banned os.%s" % node.attr)
        # Must not reference the decompiled tree or network hosts.
        self.assertNotIn("targets/c900/decompiled", src)
        self.assertNotIn("http://", src)
        self.assertNotIn("https://", src)
        # bleak is imported only inside _bleak(), never at module top for side effects
        self.assertIn("import bleak as _b", src)


class ScanMode(unittest.TestCase):
    def setUp(self):
        install_fake()

    def test_scan_readonly(self):
        rc = probe.main(["scan", "--seconds", "0.01", "--log-dir", tempfile.mkdtemp()], confirm_fn=lambda p: "")
        self.assertEqual(rc, 0)
        self.assertEqual(FakeClient.instances, [])  # no connect


class DeepPass1Fixes(unittest.TestCase):
    """Second independent review (tasks/results/DEEP-PASS-1.md). Each test fails on the pre-fix probe."""

    def setUp(self):
        install_fake()
        self.logdir = tempfile.mkdtemp()

    def _log(self):
        names = sorted(os.listdir(self.logdir))
        return "".join(open(os.path.join(self.logdir, n)).read() for n in names)

    def _run(self, cls, argv, confirm="find"):
        FakeBleak.BleakClient = cls
        try:
            return probe.main(argv + ["--log-dir", self.logdir], confirm_fn=lambda p: confirm)
        finally:
            FakeBleak.BleakClient = FakeClient

    def test_pair_state_none_when_stack_has_no_bond_api(self):
        class NoAttr:
            pass

        class Raises:
            @property
            def is_paired(self):
                raise NotImplementedError

        self.assertIsNone(probe.pair_state(NoAttr()))
        self.assertIsNone(probe.pair_state(Raises()))
        self.assertFalse(probe.pair_state(NS(is_paired=False)))

    def test_inspect_on_bleak3_like_client_says_detection_unavailable(self):
        class Bleak3Client(FakeClient):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                del self.is_paired  # bleak 3.0.2 BleakClient has no is_paired

            def __getattribute__(self, name):
                if name == "is_paired":
                    raise AttributeError(name)
                return object.__getattribute__(self, name)

        rc = self._run(Bleak3Client, ["inspect", "--address", "AA:BB:CC:DD:EE:01", "--listen", "0.05"])
        self.assertEqual(rc, 0)
        self.assertIn("pairing detection unavailable", self._log())

    def test_scan_log_hides_third_party_names_and_mfg_tail(self):
        rc = probe.main(["scan", "--seconds", "0.01", "--log-dir", self.logdir], confirm_fn=lambda p: "")
        self.assertEqual(rc, 0)
        text = self._log()
        self.assertIn("C900-Test", text)
        self.assertNotIn("'Other'", text)
        self.assertIn("<redacted len=5>", text)
        self.assertNotIn("aabbccddeeff1234", text)   # could hold the watch MAC (PROTOCOL section 3)
        self.assertIn("0102:len=8:aabb..", text)
        self.assertNotIn("AA:BB:CC:DD:EE:01", text)

    def test_serial_redacted_and_feature_hex_logged(self):
        class C(FakeClient):
            async def read_gatt_char(self, uuid):
                if _u(uuid).startswith("00002a25"):
                    return b"SN0123456789"
                return await super().read_gatt_char(uuid)

        rc = self._run(C, ["inspect", "--address", "AA:BB:CC:DD:EE:01", "--listen", "0.05"])
        self.assertEqual(rc, 0)
        text = self._log()
        self.assertNotIn("SN0123456789", text)
        self.assertIn("2a25 value=<redacted len=12>", text)
        self.assertIn("hex=aa00", text)
        self.assertIn("protocol_major=1", text)

    def test_notify_uuid_under_ota_service_refused(self):
        svcs = FakeClient("x")._default_services()
        svcs.append(FakeSvc("0000ff00-0000-1000-8000-00805f9b34fb", [FakeChar(probe.NOTIFY_UUID, ["notify"])]))
        with self.assertRaises(probe.SafetyError):
            probe.command_chars(svcs)

    def test_writes_bind_to_command_service_object(self):
        """A duplicate write UUID in another (non-OTA) service is never the target."""
        decoy = FakeChar(probe.WRITE_UUID, ["write-without-response"])
        svcs = [FakeSvc("0000abcd-0000-1000-8000-00805f9b34fb", [decoy])] + FakeClient("x")._default_services()
        w, n = probe.command_chars(svcs)
        self.assertIsNot(w, decoy)
        self.assertEqual(probe.norm_uuid(w.uuid), probe.WRITE_UUID)
        two = FakeClient("x")._default_services()
        two[0].characteristics.append(FakeChar(probe.WRITE_UUID, ["write"]))
        with self.assertRaises(probe.SafetyError):
            probe.command_chars(two)

    def test_write_is_without_response_like_the_app(self):
        rc = self._run(FakeClient, ["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "message",
                                    "--i-approve-writes"], confirm="message")
        self.assertEqual(rc, 0)
        self.assertEqual(FakeClient.instances[-1].write_responses, [False, False])  # 2 pieces

    def test_protocol_version_mismatch_refuses_before_any_write(self):
        for value in (b"V2.0", b"", b"garbage"):
            class C(FakeClient):
                async def read_gatt_char(self, uuid, _v=value):
                    if _u(uuid).startswith("00002a27"):
                        return _v
                    return await super().read_gatt_char(uuid)

            rc = self._run(C, ["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                               "--i-approve-writes"])
            self.assertEqual(rc, probe.EXIT_SAFETY, value)
            self.assertEqual(FakeClient.instances[-1].writes, [], value)
            self.assertEqual(FakeClient.instances[-1].write_responses, [], value)

    def test_protocol_major_parsing(self):
        self.assertEqual(probe.protocol_major(b"V1.2"), 1)
        self.assertEqual(probe.protocol_major(b"v3"), 3)
        self.assertEqual(probe.protocol_major(b"1.0.7"), 1)
        self.assertIsNone(probe.protocol_major(b"HW-A"))
        self.assertIsNone(probe.protocol_major(None))

    def test_ack_before_write_is_not_taken_as_answer(self):
        class Stale(FakeClient):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self._auto_ack = False

            async def start_notify(self, uuid, cb):
                await super().start_notify(uuid, cb)
                cb(None, frames.ack(0x02, 0x0B))  # matching ack before anything was sent

        old = probe.ACK_TIMEOUT_S
        probe.ACK_TIMEOUT_S = 0.3
        try:
            rc = self._run(Stale, ["safe-write", "--address", "AA:BB:CC:DD:EE:01", "--command", "find",
                                   "--i-approve-writes"])
        finally:
            probe.ACK_TIMEOUT_S = old
        self.assertEqual(rc, probe.EXIT_SAFETY)
        self.assertNotIn("ACK ok", self._log())
        self.assertIn("ack timeout", self._log())

    def test_inbound_flood_aborts(self):
        r = probe.FrameReader()
        with self.assertRaises(probe.SafetyError):
            for _ in range(probe.MAX_INBOUND_FRAMES + 1):
                r.feed(frames.ack(0x02, 0x01))
        r = probe.FrameReader()
        with self.assertRaises(probe.SafetyError):
            for _ in range(probe.MAX_INBOUND_BYTES // 1000 + 2):
                r.feed(b"\x00" * 1000)
        self.assertLessEqual(len(r.buf), 1024)

    def test_flood_during_inspect_stops_session(self):
        class Flood(FakeClient):
            async def start_notify(self, uuid, cb):
                await super().start_notify(uuid, cb)
                for _ in range(probe.MAX_INBOUND_FRAMES + 5):
                    cb(None, frames.ack(0x02, 0x01))

        rc = self._run(Flood, ["inspect", "--address", "AA:BB:CC:DD:EE:01", "--listen", "1"])
        self.assertEqual(rc, probe.EXIT_SAFETY)
        self.assertIn("inbound flood", self._log())
        self.assertLess(self._log().count("RX ack"), probe.MAX_INBOUND_FRAMES + 1)

    def test_log_dir_inside_repo_must_be_captures(self):
        with self.assertRaises(probe.SafetyError):
            probe.check_log_dir(os.path.join(ROOT, "tools"))
        with self.assertRaises(probe.SafetyError):
            probe.check_log_dir(os.path.join(ROOT, "captures", "..", "docs"))
        probe.check_log_dir(os.path.join(ROOT, "captures", "session1"))  # allowed, not created
        probe.check_log_dir(self.logdir)                                  # outside the repo: allowed
        rc = probe.main(["scan", "--seconds", "0.01", "--log-dir", os.path.join(ROOT, "docs")],
                        confirm_fn=lambda p: "")
        self.assertEqual(rc, probe.EXIT_USAGE)

    def test_log_never_overwrites(self):
        a = probe.SessionLog("scan", self.logdir)
        b = probe.SessionLog("scan", self.logdir)
        self.assertNotEqual(a.path, b.path)
        a.close(); b.close()

    def test_target_address_masked_in_error_text(self):
        cb_uuid = "1A2B3C4D-1111-2222-3333-444455556666"   # macOS CoreBluetooth style address
        log = probe.SessionLog("inspect", self.logdir)
        log.add_secret(cb_uuid)
        log.emit("ERROR Device with address %s was not found" % cb_uuid.lower())
        log.close()
        self.assertNotIn(cb_uuid.lower(), self._log().lower())

    def test_sanitize_strips_bidi_and_c1(self):
        out = probe.sanitize("C900\u202eevil\x9b31m")
        self.assertNotIn("\u202e", out)
        self.assertNotIn("\x9b", out)

    def test_time_args_bounded(self):
        for bad in (["scan", "--seconds", "0"], ["scan", "--seconds", "nan"], ["scan", "--seconds", "1e9"],
                    ["inspect", "--address", "X", "--listen", "151"]):
            with self.assertRaises(SystemExit):
                probe.build_parser().parse_args(bad)


if __name__ == "__main__":
    unittest.main()
