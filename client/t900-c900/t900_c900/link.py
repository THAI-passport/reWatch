"""Abstract link layer, RecordingLink for dry runs/simulations, and BleakLink for hardware."""
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple
from .models import is_service_prohibited


class Link(Protocol):
    """Abstract link interface for smartwatch communication."""

    @property
    def is_connected(self) -> bool:
        ...

    @property
    def mtu(self) -> int:
        ...

    async def connect(self) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def discover_services(self) -> List[str]:
        ...

    async def start_notify(self, char_uuid: str, callback: Callable[[bytes], None]) -> None:
        ...

    async def stop_notify(self, char_uuid: str) -> None:
        ...

    async def write(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        ...

    async def read(self, char_uuid: str) -> bytes:
        ...


class RecordingLink:
    """In-memory recording link used for tests, dry-runs, and software simulation."""

    def __init__(self, services: Optional[List[str]] = None, mtu: int = 128) -> None:
        self._connected = False
        self._mtu = mtu
        self._services = services or []
        self._callbacks: Dict[str, Callable[[bytes], None]] = {}
        self.writes: List[Tuple[str, bytes, bool]] = []
        self.notifications_sent: List[Tuple[str, bytes]] = []
        self.simulator: Optional[Any] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def mtu(self) -> int:
        return self._mtu

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False
        self._callbacks.clear()

    async def discover_services(self) -> List[str]:
        return list(self._services)

    async def start_notify(self, char_uuid: str, callback: Callable[[bytes], None]) -> None:
        self._callbacks[char_uuid.lower()] = callback

    async def stop_notify(self, char_uuid: str) -> None:
        self._callbacks.pop(char_uuid.lower(), None)

    async def write(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        if is_service_prohibited(char_uuid):
            raise RuntimeError(f"HARD BLOCKED: Attempted write to prohibited hazard service {char_uuid}")
        self.writes.append((char_uuid, data, response))
        if self.simulator is not None:
            await self.simulator.handle_write(char_uuid, data)

    async def read(self, char_uuid: str) -> bytes:
        if is_service_prohibited(char_uuid):
            raise RuntimeError(f"HARD BLOCKED: Attempted read of prohibited hazard service {char_uuid}")
        if self.simulator is not None:
            return await self.simulator.handle_read(char_uuid)
        # Default battery return if battery service queried
        if "2a19" in char_uuid.lower():
            return bytes([85])  # 85% battery
        return b""

    def simulate_incoming_notification(self, char_uuid: str, data: bytes) -> None:
        """Deliver a notification to registered subscriber."""
        self.notifications_sent.append((char_uuid, data))
        cb = self._callbacks.get(char_uuid.lower())
        if cb is not None:
            cb(data)


class BleakLink:
    """Concrete Link implementation backed by Bleak for real Bluetooth hardware."""

    def __init__(self, address: str) -> None:
        self.address = address
        self._client: Optional[Any] = None
        self._mtu = 23

    @property
    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    @property
    def mtu(self) -> int:
        return self._mtu

    async def connect(self) -> None:
        try:
            import bleak
        except ImportError as exc:
            raise RuntimeError("bleak is required for hardware BLE connectivity (pip install bleak)") from exc

        self._client = bleak.BleakClient(self.address)
        await self._client.connect()
        try:
            self._mtu = getattr(self._client, "mtu_size", 23)
        except Exception:
            self._mtu = 23

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def discover_services(self) -> List[str]:
        if not self._client:
            raise RuntimeError("Link not connected")
        services = []
        for service in self._client.services:
            services.append(service.uuid)
        return services

    async def start_notify(self, char_uuid: str, callback: Callable[[bytes], None]) -> None:
        if not self._client:
            raise RuntimeError("Link not connected")
        if is_service_prohibited(char_uuid):
            raise RuntimeError(f"HARD BLOCKED: Prohibited service notification {char_uuid}")

        def _handler(_sender: Any, data: bytearray) -> None:
            callback(bytes(data))

        await self._client.start_notify(char_uuid, _handler)

    async def stop_notify(self, char_uuid: str) -> None:
        if self._client:
            await self._client.stop_notify(char_uuid)

    async def write(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        if not self._client:
            raise RuntimeError("Link not connected")
        if is_service_prohibited(char_uuid):
            raise RuntimeError(f"HARD BLOCKED: Attempted write to prohibited hazard service {char_uuid}")
        await self._client.write_gatt_char(char_uuid, data, response=response)

    async def read(self, char_uuid: str) -> bytes:
        if not self._client:
            raise RuntimeError("Link not connected")
        if is_service_prohibited(char_uuid):
            raise RuntimeError(f"HARD BLOCKED: Attempted read of prohibited hazard service {char_uuid}")
        res = await self._client.read_gatt_char(char_uuid)
        return bytes(res)
