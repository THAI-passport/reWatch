"""Smartwatch async session state machine."""
import asyncio
import datetime
from typing import Any, Callable, Dict, List, Optional
from .codecs import (
    build_metadata_query,
    build_notification_alert,
    build_time_sync,
    build_jieli_frame,
    parse_hryfine_frame,
    parse_jieli_frame,
)
from .link import Link
from .models import DeviceProfile, get_profile, is_service_prohibited
from .safe_write import SafeWriteGuard


class SmartwatchSession:
    """Async session managing connection, status queries, time sync, and dial upload."""

    def __init__(
        self,
        link: Link,
        profile: Optional[DeviceProfile] = None,
        safe_write: Optional[SafeWriteGuard] = None,
        address: str = "00:00:00:00:00:00",
        dry_run: bool = False,
    ) -> None:
        self.link = link
        self.profile = profile or get_profile("c900-ultra")
        self.safe_write = safe_write or SafeWriteGuard()
        self.address = address
        self.dry_run = dry_run
        self.telemetry: List[str] = []
        self._notify_events: Dict[int, asyncio.Event] = {}
        self._latest_responses: Dict[int, Any] = {}
        self._connected = False

    def _log_telemetry(self, msg: str) -> None:
        prefix = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}]"
        self.telemetry.append(f"{prefix} {msg}")

    def _on_notification(self, data: bytes) -> None:
        self._log_telemetry(f"RX notify ({len(data)} B): {data.hex().upper()}")
        if self.profile.transport_family == "hryfine_nus":
            try:
                parsed = parse_hryfine_frame(data)
                cmd = parsed.get("cmd", 0)
                self._latest_responses[cmd] = parsed
                if cmd in self._notify_events:
                    self._notify_events[cmd].set()
            except Exception as e:
                self._log_telemetry(f"Parse error: {e}")
        elif self.profile.transport_family == "jieli_rcsp":
            try:
                parsed = parse_jieli_frame(data)
                opcode = parsed.get("opcode", 0)
                self._latest_responses[opcode] = parsed
                if opcode in self._notify_events:
                    self._notify_events[opcode].set()
            except Exception as e:
                self._log_telemetry(f"JieLi parse error: {e}")

    async def connect(self) -> None:
        """Establish connection, discover services, and configure notification CCCD."""
        self._log_telemetry(f"Connecting to device {self.address} (dry_run={self.dry_run})...")
        await self.link.connect()

        # Discover services and negotiate transport
        services = await self.link.discover_services()
        self._log_telemetry(f"Discovered {len(services)} services")

        for s in services:
            if is_service_prohibited(s):
                self._log_telemetry(f"WARNING: Prohibited OTA service detected: {s}")

        # Dynamic profile selection based on discovered services
        svc_lower = [s.lower() for s in services]
        if any("6e400001" in s for s in svc_lower):
            if any("b5a3-f393-e0a9-e50e24dcca9f" in s for s in svc_lower):
                self.profile = get_profile("c900-ultra")
            elif any("b5a9-f393-e0a9-e50e24dcca9e" in s for s in svc_lower):
                self.profile = get_profile("c900-std-nus")
        elif any("0000ae00" in s for s in svc_lower):
            self.profile = get_profile("t900-ultra")

        # Start notifications
        await self.link.start_notify(self.profile.notify_uuid, self._on_notification)
        self._connected = True
        self._log_telemetry(f"Session established with profile {self.profile.name}")

    async def disconnect(self) -> None:
        """Tear down active session."""
        if self._connected:
            await self.link.stop_notify(self.profile.notify_uuid)
            await self.link.disconnect()
            self._connected = False
            self._log_telemetry("Session disconnected")

    async def probe(self) -> Dict[str, Any]:
        """Perform non-destructive read-only probe of device identifiers."""
        report: Dict[str, Any] = {
            "address": self.address,
            "profile": self.profile.name,
            "transport": self.profile.transport_family,
            "mtu": self.link.mtu,
            "battery_percent": None,
            "model_string": None,
            "firmware_string": None,
        }

        # Read standard Battery characteristic 0x2A19
        try:
            bat_raw = await self.link.read("00002a19-0000-1000-8000-00805f9b34fb")
            if bat_raw:
                report["battery_percent"] = bat_raw[0]
        except Exception:
            pass

        # Read Model 0x2A24
        try:
            mod_raw = await self.link.read("00002a24-0000-1000-8000-00805f9b34fb")
            if mod_raw:
                report["model_string"] = mod_raw.decode("utf-8", errors="replace").strip()
        except Exception:
            pass

        # Read Firmware 0x2A26
        try:
            fw_raw = await self.link.read("00002a26-0000-1000-8000-00805f9b34fb")
            if fw_raw:
                report["firmware_string"] = fw_raw.decode("utf-8", errors="replace").strip()
        except Exception:
            pass

        self._log_telemetry(f"Probe completed: battery={report['battery_percent']}%, model={report['model_string']}")
        return report

    async def read_status(self) -> Dict[str, Any]:
        """Query device status (battery and metadata)."""
        probe_res = await self.probe()
        if self.profile.transport_family == "hryfine_nus":
            query = build_metadata_query()
            ev = asyncio.Event()
            self._notify_events[0xF3] = ev
            await self.link.write(self.profile.write_uuid, query)
            try:
                await asyncio.wait_for(ev.wait(), timeout=2.0)
                probe_res["vendor_status"] = "OK"
            except asyncio.TimeoutError:
                probe_res["vendor_status"] = "TIMEOUT"
            finally:
                self._notify_events.pop(0xF3, None)
        elif self.profile.transport_family == "jieli_rcsp":
            req = build_jieli_frame(flag=0xC0, opcode=0x02, body=bytes([0x01]))
            ev = asyncio.Event()
            self._notify_events[0x02] = ev
            await self.link.write(self.profile.write_uuid, req)
            try:
                await asyncio.wait_for(ev.wait(), timeout=2.0)
                probe_res["vendor_status"] = "OK"
            except asyncio.TimeoutError:
                probe_res["vendor_status"] = "TIMEOUT"
            finally:
                self._notify_events.pop(0x02, None)

        return probe_res

    async def sync_time(self, dt: Optional[datetime.datetime] = None) -> bool:
        """Synchronize system time with device clock."""
        if dt is None:
            dt = datetime.datetime.now()

        if self.profile.transport_family == "hryfine_nus":
            pkt = build_time_sync(dt)
            allowed, reason = self.safe_write.check_allowed(
                self.address, pkt, allow_identical=True, dry_run=self.dry_run
            )
            if not allowed:
                self._log_telemetry(f"Safe-write block: {reason}")
                return False

            ev = asyncio.Event()
            self._notify_events[0x02] = ev
            await self.link.write(self.profile.write_uuid, pkt)

            success = False
            try:
                await asyncio.wait_for(ev.wait(), timeout=3.0)
                resp = self._latest_responses.get(0x02, {})
                success = resp.get("status") == 0x01
            except asyncio.TimeoutError:
                self._log_telemetry("Time sync timeout awaiting 0xFD ACK")
            finally:
                self._notify_events.pop(0x02, None)

            if success:
                self.safe_write.record_success(self.address, pkt, dry_run=self.dry_run)
            return success
        return True

    async def push_notification(self, app_id: int, title: str, message: str) -> bool:
        """Push an alert notification to the watch display."""
        if self.profile.transport_family == "hryfine_nus":
            pkt = build_notification_alert(app_id, title, message)
            allowed, reason = self.safe_write.check_allowed(
                self.address, pkt, allow_identical=False, dry_run=self.dry_run
            )
            if not allowed:
                self._log_telemetry(f"Safe-write block: {reason}")
                return False

            ev = asyncio.Event()
            self._notify_events[0x05] = ev
            await self.link.write(self.profile.write_uuid, pkt)

            success = False
            try:
                await asyncio.wait_for(ev.wait(), timeout=3.0)
                resp = self._latest_responses.get(0x05, {})
                success = resp.get("status") == 0x01
            except asyncio.TimeoutError:
                self._log_telemetry("Notification timeout awaiting ACK")
            finally:
                self._notify_events.pop(0x05, None)

            if success:
                self.safe_write.record_success(self.address, pkt, dry_run=self.dry_run)
            return success
        return True

    async def push_dial(
        self,
        dial_data: bytes,
        allow_identical: bool = False,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """Push a compiled watch face dial package with chunking and safe-write guard."""
        allowed, reason = self.safe_write.check_allowed(
            self.address, dial_data, allow_identical=allow_identical, dry_run=self.dry_run
        )
        if not allowed:
            self._log_telemetry(f"Safe-write blocked dial push: {reason}")
            return False

        chunk_size = self.profile.chunk_size
        total_len = len(dial_data)
        offset = 0

        self._log_telemetry(f"Starting dial push ({total_len} bytes in {chunk_size}B chunks)...")

        while offset < total_len:
            chunk = dial_data[offset:offset + chunk_size]
            if self.profile.transport_family == "hryfine_nus":
                from .codecs import build_hryfine_frame
                pkt = build_hryfine_frame(cmd=0x1A, sub=0x01, payload=chunk)
                ev = asyncio.Event()
                self._notify_events[0x1A] = ev
                await self.link.write(self.profile.write_uuid, pkt)
                try:
                    await asyncio.wait_for(ev.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    self._log_telemetry(f"Timeout awaiting dial chunk ACK at offset {offset}")
                    return False
                finally:
                    self._notify_events.pop(0x1A, None)

            offset += len(chunk)
            if progress_cb:
                progress_cb(offset, total_len)
            if not self.dry_run and hasattr(self.link, "_client"):
                await asyncio.sleep(0.01)

        self.safe_write.record_success(self.address, dial_data, dry_run=self.dry_run)
        self._log_telemetry("Dial push transfer completed successfully")
        return True
