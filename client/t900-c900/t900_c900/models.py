"""Device profile specifications and hazard blacklists."""
from dataclasses import dataclass
from typing import Dict, List, Optional

PROHIBITED_SERVICES: List[str] = [
    # Bluetrum Cus5610 OTA Bootloader service - writing bricks devices permanently
    "000018a8-0000-1000-8000-00805f9b34fb",
    "18a8",
    # JieLi OTA bootloader services
    "0000ae10-0000-1000-8000-00805f9b34fb",
    "ae10",
    "0000ae20-0000-1000-8000-00805f9b34fb",
    "ae20",
]


@dataclass(frozen=True)
class DeviceProfile:
    id: str
    name: str
    transport_family: str  # "hryfine_nus" or "jieli_rcsp"
    service_uuid: str
    write_uuid: str
    notify_uuid: str
    display_width: int
    display_height: int
    chunk_size: int
    default_app: str


PROFILES: Dict[str, DeviceProfile] = {
    "c900-ultra": DeviceProfile(
        id="c900-ultra",
        name="C900 Ultra",
        transport_family="hryfine_nus",
        service_uuid="6E400001-B5A3-F393-E0A9-E50E24DCCA9F",
        write_uuid="6E400002-B5A3-F393-E0A9-E50E24DCCA9F",
        notify_uuid="6E400003-B5A3-F393-E0A9-E50E24DCCA9F",
        display_width=240,
        display_height=286,
        chunk_size=128,
        default_app="HryFine",
    ),
    "c900-promax": DeviceProfile(
        id="c900-promax",
        name="C900 Pro Max",
        transport_family="hryfine_nus",
        service_uuid="6E400001-B5A3-F393-E0A9-E50E24DCCA9F",
        write_uuid="6E400002-B5A3-F393-E0A9-E50E24DCCA9F",
        notify_uuid="6E400003-B5A3-F393-E0A9-E50E24DCCA9F",
        display_width=320,
        display_height=385,
        chunk_size=128,
        default_app="HryFine",
    ),
    "c900-std-nus": DeviceProfile(
        id="c900-std-nus",
        name="C900 Standard Nordic NUS",
        transport_family="hryfine_nus",
        service_uuid="6E400001-B5A9-F393-E0A9-E50E24DCCA9E",
        write_uuid="6E400002-B5A9-F393-E0A9-E50E24DCCA9E",
        notify_uuid="6E400003-B5A9-F393-E0A9-E50E24DCCA9E",
        display_width=240,
        display_height=286,
        chunk_size=128,
        default_app="HryFine",
    ),
    "t900-ultra": DeviceProfile(
        id="t900-ultra",
        name="T900 Ultra",
        transport_family="jieli_rcsp",
        service_uuid="0000AE00-0000-1000-8000-00805F9B34FB",
        write_uuid="0000AE01-0000-1000-8000-00805F9B34FB",
        notify_uuid="0000AE02-0000-1000-8000-00805F9B34FB",
        display_width=240,
        display_height=286,
        chunk_size=128,
        default_app="HiWatch Pro",
    ),
    "t900-ultra2": DeviceProfile(
        id="t900-ultra2",
        name="T900 Ultra 2",
        transport_family="jieli_rcsp",
        service_uuid="0000AE00-0000-1000-8000-00805F9B34FB",
        write_uuid="0000AE01-0000-1000-8000-00805F9B34FB",
        notify_uuid="0000AE02-0000-1000-8000-00805F9B34FB",
        display_width=320,
        display_height=385,
        chunk_size=128,
        default_app="HiWatch Pro",
    ),
}


def get_profile(profile_id: str) -> DeviceProfile:
    """Retrieve profile by ID or raise ValueError."""
    key = profile_id.lower().strip()
    if key in PROFILES:
        return PROFILES[key]
    raise ValueError(f"Unknown device profile '{profile_id}'. Available: {list(PROFILES.keys())}")


def is_service_prohibited(uuid_str: str) -> bool:
    """Check if a service UUID belongs to the hazardous OTA blacklist."""
    cleaned = uuid_str.lower().strip()
    for prohibited in PROHIBITED_SERVICES:
        if prohibited in cleaned:
            return True
    return False
