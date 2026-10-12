"""Command-line interface for T900 and C900 smartwatch operations."""
import argparse
import asyncio
import datetime
import json
import sys
from typing import List, Optional
from .dial import compile_dial_package
from .link import BleakLink, RecordingLink
from .models import PROFILES, get_profile
from .safe_write import SafeWriteGuard
from .session import SmartwatchSession
from .simulator import SmartwatchSimulator


async def run_probe(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    if args.dry_run or args.simulate:
        link = RecordingLink(services=[profile.service_uuid], mtu=128)
        sim = SmartwatchSimulator(profile=profile, link=link)
    else:
        link = BleakLink(args.address)

    session = SmartwatchSession(link=link, profile=profile, address=args.address, dry_run=args.dry_run)
    try:
        await session.connect()
        report = await session.probe()
        if args.qualify or args.json:
            print(json.dumps(report, indent=2))
        else:
            print("--- Watch Probe Report (Read-Only) ---")
            print(f"Device Address : {report['address']}")
            print(f"Profile        : {report['profile']}")
            print(f"Transport      : {report['transport']}")
            print(f"MTU            : {report['mtu']}")
            print(f"Battery Level  : {report['battery_percent']}%")
            print(f"Model String   : {report['model_string']}")
            print(f"Firmware       : {report['firmware_string']}")
            print("Status         : READ_ONLY_PROBE_SUCCESS")
        return 0
    finally:
        await session.disconnect()


async def run_status(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    if args.dry_run or args.simulate:
        link = RecordingLink(services=[profile.service_uuid], mtu=128)
        sim = SmartwatchSimulator(profile=profile, link=link)
    else:
        link = BleakLink(args.address)

    session = SmartwatchSession(link=link, profile=profile, address=args.address, dry_run=args.dry_run)
    try:
        await session.connect()
        res = await session.read_status()
        print(json.dumps(res, indent=2) if args.json else f"Battery: {res['battery_percent']}%, Vendor status: {res.get('vendor_status', 'OK')}")
        return 0
    finally:
        await session.disconnect()


async def run_time_sync(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    if args.dry_run or args.simulate:
        link = RecordingLink(services=[profile.service_uuid], mtu=128)
        sim = SmartwatchSimulator(profile=profile, link=link)
    else:
        link = BleakLink(args.address)

    guard = SafeWriteGuard()
    session = SmartwatchSession(link=link, profile=profile, safe_write=guard, address=args.address, dry_run=args.dry_run)
    try:
        await session.connect()
        ok = await session.sync_time()
        print("Time sync result:", "SUCCESS" if ok else "FAILED")
        return 0 if ok else 1
    finally:
        await session.disconnect()


async def run_notify(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    if args.dry_run or args.simulate:
        link = RecordingLink(services=[profile.service_uuid], mtu=128)
        sim = SmartwatchSimulator(profile=profile, link=link)
    else:
        link = BleakLink(args.address)

    guard = SafeWriteGuard()
    session = SmartwatchSession(link=link, profile=profile, safe_write=guard, address=args.address, dry_run=args.dry_run)
    try:
        await session.connect()
        ok = await session.push_notification(app_id=args.app_id, title=args.title, message=args.message)
        print("Notification result:", "SUCCESS" if ok else "FAILED")
        return 0 if ok else 1
    finally:
        await session.disconnect()


async def run_push_dial(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    dial_bytes = compile_dial_package(width=profile.display_width, height=profile.display_height)

    if args.dry_run or args.simulate:
        link = RecordingLink(services=[profile.service_uuid], mtu=128)
        sim = SmartwatchSimulator(profile=profile, link=link)
    else:
        link = BleakLink(args.address)

    guard = SafeWriteGuard()
    session = SmartwatchSession(link=link, profile=profile, safe_write=guard, address=args.address, dry_run=args.dry_run)
    try:
        await session.connect()

        def _on_progress(cur: int, total: int) -> None:
            pct = (cur / total) * 100
            print(f"\rUploading dial: {cur}/{total} bytes ({pct:.1f}%)", end="", flush=True)

        ok = await session.push_dial(dial_bytes, allow_identical=args.no_delta, progress_cb=_on_progress)
        print()
        print("Dial upload result:", "SUCCESS" if ok else "FAILED")
        return 0 if ok else 1
    finally:
        await session.disconnect()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="reWatch client CLI for T900 and C900 smartwatches")
    parser.add_argument("--profile", default="c900-ultra", choices=list(PROFILES.keys()), help="Target device profile")
    parser.add_argument("--address", default="00:11:22:33:44:55", help="Target Bluetooth MAC / UUID")
    parser.add_argument("--dry-run", action="store_true", help="Execute without modifying real device state")
    parser.add_argument("--simulate", action="store_true", help="Use software device simulator")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    sub = parser.add_subparsers(dest="command", required=True)

    # probe
    p_probe = sub.add_parser("probe", help="Perform non-destructive read-only device probe")
    p_probe.add_argument("--qualify", action="store_true", help="Generate hardware qualification report")

    # status
    sub.add_parser("status", help="Read device battery and vendor status")

    # time-sync
    sub.add_parser("time-sync", help="Synchronize watch clock with host time")

    # notify
    p_notif = sub.add_parser("notify", help="Push an alert notification to the watch display")
    p_notif.add_argument("--app-id", type=int, default=1, help="Notification app ID (1=SMS, 2=Call, etc.)")
    p_notif.add_argument("--title", default="Alert", help="Notification title")
    p_notif.add_argument("--message", default="Test alert from reWatch", help="Notification message text")

    # push-dial
    p_dial = sub.add_parser("push-dial", help="Upload a watch face dial package")
    p_dial.add_argument("--no-delta", action="store_true", help="Bypass delta skip to allow identical upload")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler_map = {
        "probe": run_probe,
        "status": run_status,
        "time-sync": run_time_sync,
        "notify": run_notify,
        "push-dial": run_push_dial,
    }

    handler = handler_map.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return asyncio.run(handler(args))


if __name__ == "__main__":
    sys.exit(main())
