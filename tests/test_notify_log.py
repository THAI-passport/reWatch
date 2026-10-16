import asyncio
import os
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import notify_log  # noqa: E402


class FakeClient:
    def __init__(self):
        self.services = [NS(characteristics=[NS(uuid="000001f2-0000-1000-8000-00805f9b34fb", properties=["notify"]),
                                              NS(uuid="000001f1-0000-1000-8000-00805f9b34fb", properties=["write-without-response"])])]
        self.handlers, self.stopped = {}, []

    async def start_notify(self, uuid, cb):
        self.handlers[uuid] = cb

    async def stop_notify(self, uuid):
        self.stopped.append(uuid)


class NotifyLog(unittest.TestCase):
    def test_subscribes_only_to_notifiable_and_logs_events(self):
        c, events = FakeClient(), []

        async def fake_sleep(_):
            for cb in c.handlers.values():
                cb(None, bytearray(b"\xa0\x01\x02"))

        subs = asyncio.run(notify_log.log_notifications(c, 1, events.append, sleep=fake_sleep))
        self.assertEqual(len(subs), 1)
        self.assertTrue(subs[0].startswith("000001f2"))
        self.assertEqual(events[0]["hex"], "a00102")
        self.assertEqual(events[0]["len"], 3)
        self.assertEqual(c.stopped, subs)

    def test_mask_hides_last_three_bytes(self):
        self.assertEqual(notify_log.mask("AA:BB:CC:DD:EE:FF"), "AA:BB:CC:xx:xx:xx")
        self.assertIn("...", notify_log.mask("2B1F8A2C-3C0B-4C5E-9D2A-1234567890AB"))


CMD = "6e400003-b5a3-f393-e0a9-e50e24dcca9f"


class C900Client(FakeClient):
    """Fake C900 GATT table: command service plus the three OTA services and battery."""
    def __init__(self):
        super().__init__()
        n = lambda u: NS(uuid=u, properties=["notify"])  # noqa: E731
        self.services = [
            NS(uuid="6e400001-b5a3-f393-e0a9-e50e24dcca9f", characteristics=[n(CMD), NS(uuid="6e400002-b5a3-f393-e0a9-e50e24dcca9f", properties=["write-without-response"])]),
            NS(uuid="0000ff00-0000-1000-8000-00805f9b34fb", characteristics=[n("0000ff01-0000-1000-8000-00805f9b34fb"), n("0000ff03-0000-1000-8000-00805f9b34fb")]),
            NS(uuid="000018a8-0000-1000-8000-00805f9b34fb", characteristics=[n("00002aa8-0000-1000-8000-00805f9b34fb")]),
            NS(uuid="6e40ff01-b5a3-f393-e0a9-e50e24dcca9e", characteristics=[n("6e40ff03-b5a3-f393-e0a9-e50e24dcca9e")]),
            NS(uuid="0000180f-0000-1000-8000-00805f9b34fb", characteristics=[n("00002a19-0000-1000-8000-00805f9b34fb")]),
            NS(uuid="0000abcd-0000-1000-8000-00805f9b34fb", characteristics=[n("0000beef-0000-1000-8000-00805f9b34fb")]),
        ]


async def _nosleep(_):
    return None


class OtaSafety(unittest.TestCase):
    def run_log(self, c, **kw):
        return asyncio.run(notify_log.log_notifications(c, 0, [].append, sleep=_nosleep, announce=lambda _m: None, **kw))

    def test_default_skips_all_ota_characteristics(self):
        c = C900Client()
        subs = self.run_log(c)
        self.assertEqual(sorted(subs), sorted([CMD, "00002a19-0000-1000-8000-00805f9b34fb", "0000beef-0000-1000-8000-00805f9b34fb"]))
        for u in c.handlers:
            self.assertFalse(notify_log.is_denied(u), u)

    def test_only_subscribes_exactly_one(self):
        c = C900Client()
        self.assertEqual(self.run_log(c, only=[CMD.upper()]), [CMD])
        self.assertEqual(list(c.handlers), [CMD])

    def test_denied_uuid_in_only_raises_before_any_subscribe(self):
        c = C900Client()
        with self.assertRaises(notify_log.DeniedUUID):
            self.run_log(c, only=[CMD, "ff01"])
        self.assertEqual(c.handlers, {})

    def test_cli_exits_nonzero_on_denied_only(self):
        for u in ("0000FF03-0000-1000-8000-00805F9B34FB", "6e40ff03-b5a3-f393-e0a9-e50e24dcca9e", "2aa9"):
            self.assertEqual(notify_log.main(["AA:BB:CC:DD:EE:FF", "--only", u]), 2, u)

    def test_extra_deny_applies_without_only(self):
        c = C900Client()
        subs = self.run_log(c, deny=["beef"])
        self.assertNotIn("0000beef-0000-1000-8000-00805f9b34fb", subs)

    def test_announces_plan_before_listening(self):
        c, msgs = C900Client(), []
        asyncio.run(notify_log.log_notifications(c, 0, [].append, sleep=_nosleep, announce=msgs.append, only=[CMD]))
        self.assertTrue(msgs[0].startswith("will subscribe to 1"))


if __name__ == "__main__":
    unittest.main()
