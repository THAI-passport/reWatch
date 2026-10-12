"""Software device simulator implementing the smartwatch side of HryFine and JieLi protocols."""
import asyncio
from typing import Any, Dict, List, Optional
from .codecs import build_hryfine_ack, build_jieli_frame, parse_hryfine_frame, parse_jieli_frame
from .link import RecordingLink
from .models import DeviceProfile, get_profile


class SmartwatchSimulator:
    """Simulates C900 (HryFine NUS) and T900 (JieLi RCSP) watches for clean-room testing."""

    def __init__(self, profile: Optional[DeviceProfile] = None, link: Optional[RecordingLink] = None) -> None:
        self.profile = profile or get_profile("c900-ultra")
        self.battery_level = 88
        self.model_name = self.profile.name
        self.firmware_version = "v1.2.0"
        self.received_frames: List[Dict[str, Any]] = []
        self.received_notifications: List[bytes] = []
        self.received_dial_bytes = bytearray()
        self.last_synced_time: Optional[bytes] = None
        self.link = link
        if self.link is not None:
            self.link.simulator = self

    async def handle_write(self, char_uuid: str, data: bytes) -> None:
        """Process incoming write from the client session."""
        char_clean = char_uuid.lower()
        if self.profile.transport_family == "hryfine_nus":
            if char_clean == self.profile.write_uuid.lower():
                await self._handle_hryfine_write(data)
        elif self.profile.transport_family == "jieli_rcsp":
            if char_clean == self.profile.write_uuid.lower():
                await self._handle_jieli_write(data)

    async def _handle_hryfine_write(self, data: bytes) -> None:
        parsed = parse_hryfine_frame(data)
        self.received_frames.append(parsed)
        cmd = parsed["cmd"]
        sub = parsed["sub"]
        payload = parsed["payload"]

        # Yield to event loop
        await asyncio.sleep(0)

        if cmd == 0x02 and sub == 0x0A:  # Time Sync
            self.last_synced_time = payload
            ack = build_hryfine_ack(cmd=0x02, status=0x01)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, ack)

        elif cmd == 0xF3 and sub == 0x00:  # Device Info Query
            ack = build_hryfine_ack(cmd=0xF3, status=0x01)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, ack)

        elif cmd == 0x05 and sub == 0x01:  # Notification Alert
            self.received_notifications.append(payload)
            ack = build_hryfine_ack(cmd=0x05, status=0x01)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, ack)

        elif cmd == 0x1A:  # Dial transfer chunk
            self.received_dial_bytes.extend(payload)
            ack = build_hryfine_ack(cmd=0x1A, status=0x01)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, ack)

    async def _handle_jieli_write(self, data: bytes) -> None:
        parsed = parse_jieli_frame(data)
        self.received_frames.append(parsed)
        opcode = parsed["opcode"]
        body = parsed["body"]
        sn = body[0] if body else 0x01

        await asyncio.sleep(0)

        if opcode == 0x02:  # Status query
            resp_body = bytes([sn, self.battery_level, 0x01])
            resp = build_jieli_frame(flag=0x80, opcode=0x02, body=resp_body)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, resp)
        elif opcode in (0x1B, 0x21):  # Transfer prepare/start
            resp_body = bytes([sn, 0x00])  # success status 0
            resp = build_jieli_frame(flag=0x80, opcode=opcode, body=resp_body)
            if self.link is not None:
                self.link.simulate_incoming_notification(self.profile.notify_uuid, resp)

    async def handle_read(self, char_uuid: str) -> bytes:
        """Process incoming GATT read request."""
        char_clean = char_uuid.lower()
        if "2a19" in char_clean:
            return bytes([self.battery_level])
        if "2a24" in char_clean:
            return self.model_name.encode("utf-8")
        if "2a26" in char_clean:
            return self.firmware_version.encode("utf-8")
        return b""
