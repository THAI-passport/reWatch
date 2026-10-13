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
        u = str(uuid).lower()
        if probe.is_ota_uuid(u):
            raise AssertionError("test guard: start_notify on OTA uuid %s" % u)
        self.handlers[u] = cb

    async def stop_notify(self, uuid):
        self.handlers.pop(str(uuid).lower(), None)

    async def read_gatt_char(self, uuid):
        u = str(uuid).lower()
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
        u = str(uuid).lower()
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


if __name__ == "__main__":
    unittest.main()
