#!/usr/bin/env python3
"""Passive notification logger for a real device: subscribes to notifiable characteristics and prints what arrives. Writes nothing
to the device's storage (it only enables notifications, which writes the standard CCCD descriptor).

    python tools/notify_log.py ADDRESS [--seconds 60] [--json out.jsonl] [--only UUID ...] [--deny UUID ...]

OTA/DFU safety: a deny list is always applied, with or without --only. Default: services 0xFF00 and 0x18A8 (and their
characteristics 0xFF01-0xFF03, 0x2AA8, 0x2AA9) and any UUID ending in `dcca9e` (Bluetrum OTA, c900). --deny adds more.
--only UUID (repeatable) subscribes to exactly those; naming a denied UUID there exits with code 2 before anything is enabled.
The subscription list is printed before listening starts.

Use it for hardware task HW-13 (touch events) and to catch anything the device sends unprompted. Needs bleak and a Bluetooth adapter.
Output lines: seconds-since-start, characteristic uuid, length, hex. The address is never printed in full.
"""
import argparse
import asyncio
import json
import sys
import time


BASE = "-0000-1000-8000-00805f9b34fb"
DEFAULT_DENY = ("ff00", "ff01", "ff02", "ff03", "18a8", "2aa8", "2aa9")
DENY_SUFFIXES = ("dcca9e",)


class DeniedUUID(ValueError):
    pass


def norm(uuid):
    """Lower-case full 128-bit form; 4- or 8-hex-digit short UUIDs are expanded on the Bluetooth base."""
    u = str(uuid).strip().lower()
    if len(u) == 4:
        u = "0000" + u
    if len(u) == 8:
        u = u + BASE
    return u


def is_denied(uuid, deny=()):
    u = norm(uuid)
    return u in {norm(d) for d in tuple(DEFAULT_DENY) + tuple(deny)} or u.endswith(DENY_SUFFIXES)


def plan(services, only=None, deny=()):
    """Return the list of characteristic UUIDs to subscribe. Skips denied characteristics and all characteristics of denied services.
    With `only`, returns exactly those that exist; raises DeniedUUID if any `only` UUID is denied."""
    if only:
        bad = [u for u in only if is_denied(u, deny)]
        if bad:
            raise DeniedUUID("refusing to subscribe to denied OTA/DFU UUID(s): " + ", ".join(norm(u) for u in bad))
        want = {norm(u) for u in only}
    out = []
    for svc in services:
        svc_denied = is_denied(getattr(svc, "uuid", ""), deny)
        for ch in svc.characteristics:
            u = norm(ch.uuid)
            if svc_denied or is_denied(u, deny):
                continue
            if only and u not in want:
                continue
            if "notify" in ch.properties or "indicate" in ch.properties:
                out.append(u)
    return out


def mask(addr):
    return addr[:-8] + "xx:xx:xx" if len(addr) == 17 and addr.count(":") == 5 else addr[:4] + "..."


async def log_notifications(client, seconds, emit, clock=time.monotonic, sleep=asyncio.sleep, only=None, deny=(), announce=print):
    """Subscribe on `client` (a connected BleakClient-like object) to the characteristics chosen by plan(); call emit(dict) per event.
    Raises DeniedUUID before enabling anything if `only` names a denied UUID."""
    targets = plan(client.services, only, deny)
    announce("will subscribe to %d characteristic(s): %s" % (len(targets), ", ".join(targets) or "none"))
    t0 = clock()
    subscribed = []

    def handler_for(uuid):
        def handler(_sender, data):
            emit({"t": round(clock() - t0, 3), "uuid": uuid, "len": len(data), "hex": bytes(data).hex()})
        return handler

    for u in targets:
        try:
            await client.start_notify(u, handler_for(u))
            subscribed.append(u)
        except Exception as e:  # noqa: BLE001
            emit({"t": round(clock() - t0, 3), "uuid": u, "error": str(e)})
    await sleep(seconds)
    for u in subscribed:
        try:
            await client.stop_notify(u)
        except Exception:  # noqa: BLE001
            pass
    return subscribed


async def main_async(a):
    from bleak import BleakClient
    out = open(a.json, "w") if a.json else None

    def emit(ev):
        line = ("%8.3f  %s  error: %s" % (ev["t"], ev["uuid"], ev["error"])) if "error" in ev else \
               ("%8.3f  %s  len=%-4d %s" % (ev["t"], ev["uuid"], ev["len"], ev["hex"]))
        print(line, flush=True)
        if out:
            out.write(json.dumps(ev) + "\n")
    print("connecting to %s ..." % mask(a.address))
    async with BleakClient(a.address, timeout=20.0) as client:
        subs = await log_notifications(client, a.seconds, emit, only=a.only, deny=a.deny)
        print("subscribed to %d characteristic(s): %s" % (len(subs), ", ".join(subs) or "none"))
    if out:
        out.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("address", help="Bluetooth address (macOS: the UUID that your BLE scanner prints)")
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--json", help="also write one JSON object per event to this file")
    ap.add_argument("--only", action="append", metavar="UUID", help="subscribe to this characteristic only (repeatable)")
    ap.add_argument("--deny", action="append", default=[], metavar="UUID", help="extra UUID to never subscribe (added to the OTA/DFU defaults)")
    a = ap.parse_args(argv)
    bad = [u for u in (a.only or []) if is_denied(u, a.deny)]
    if bad:
        print("refusing: denied OTA/DFU UUID(s) in --only: " + ", ".join(norm(u) for u in bad), file=sys.stderr)
        return 2
    try:
        return asyncio.run(main_async(a))
    except DeniedUUID as e:
        print("refusing: %s" % e, file=sys.stderr)
        return 2
    except ImportError:
        print("bleak is not installed (pip install bleak)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
