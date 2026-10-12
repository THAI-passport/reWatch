"""Integration tests for SmartwatchSession interacting with SmartwatchSimulator."""
import asyncio
import datetime
import shutil
import tempfile
import unittest
from t900_c900.dial import compile_dial_package
from t900_c900.link import RecordingLink
from t900_c900.models import get_profile
from t900_c900.safe_write import SafeWriteGuard
from t900_c900.session import SmartwatchSession
from t900_c900.simulator import SmartwatchSimulator


class TestSessionSimulator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.guard = SafeWriteGuard(state_dir=self.temp_dir, min_interval_seconds=0.01)
        self.profile = get_profile("c900-ultra")
        self.link = RecordingLink(services=[self.profile.service_uuid], mtu=128)
        self.sim = SmartwatchSimulator(profile=self.profile, link=self.link)
        self.session = SmartwatchSession(
            link=self.link,
            profile=self.profile,
            safe_write=self.guard,
            address="11:22:33:44:55:66",
            dry_run=False,
        )
        await self.session.connect()

    async def asyncTearDown(self):
        await self.session.disconnect()
        shutil.rmtree(self.temp_dir)

    async def test_read_only_probe(self):
        report = await self.session.probe()
        self.assertEqual(report["battery_percent"], 88)
        self.assertEqual(report["model_string"], "C900 Ultra")
        self.assertEqual(report["firmware_string"], "v1.2.0")

    async def test_read_status(self):
        res = await self.session.read_status()
        self.assertEqual(res["battery_percent"], 88)
        self.assertEqual(res["vendor_status"], "OK")

    async def test_time_sync(self):
        dt = datetime.datetime(2026, 10, 12, 10, 0, 0)
        ok = await self.session.sync_time(dt)
        self.assertTrue(ok)
        self.assertIsNotNone(self.sim.last_synced_time)
        self.assertEqual(len(self.sim.last_synced_time), 7)

    async def test_notification_alert(self):
        ok = await self.session.push_notification(app_id=1, title="Test", message="Hello Watch")
        self.assertTrue(ok)
        self.assertEqual(len(self.sim.received_notifications), 1)

    async def test_dial_upload_chunking(self):
        # Create a small dial package
        dial_data = compile_dial_package(width=240, height=286)
        # Small chunk size for test
        self.session.profile = get_profile("c900-ultra")
        ok = await self.session.push_dial(dial_data[:512], allow_identical=True)
        self.assertTrue(ok)
        self.assertEqual(len(self.sim.received_dial_bytes), 512)

    async def test_prohibited_service_block(self):
        with self.assertRaises(RuntimeError) as ctx:
            await self.link.write("000018a8-0000-1000-8000-00805f9b34fb", b"\x00")
        self.assertIn("HARD BLOCKED", str(ctx.exception))


class TestJieLiSessionSimulator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.guard = SafeWriteGuard(state_dir=self.temp_dir, min_interval_seconds=0.01)
        self.profile = get_profile("t900-ultra")
        self.link = RecordingLink(services=[self.profile.service_uuid], mtu=128)
        self.sim = SmartwatchSimulator(profile=self.profile, link=self.link)
        self.session = SmartwatchSession(
            link=self.link,
            profile=self.profile,
            safe_write=self.guard,
            address="AA:BB:CC:DD:EE:FF",
            dry_run=False,
        )
        await self.session.connect()

    async def asyncTearDown(self):
        await self.session.disconnect()
        shutil.rmtree(self.temp_dir)

    async def test_jieli_status_query(self):
        res = await self.session.read_status()
        self.assertEqual(res["battery_percent"], 88)
        self.assertEqual(res["vendor_status"], "OK")


if __name__ == "__main__":
    unittest.main()
