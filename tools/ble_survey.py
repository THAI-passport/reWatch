#!/usr/bin/env python3
"""Read-only BLE survey: scan, then list GATT services and read readable characteristics.

Never writes, never subscribes to OTA services. Addresses are masked in output.
Needs bleak (pip install bleak). Works on macOS (CoreBluetooth ids), Linux (BlueZ), Windows.

  python tools/ble_survey.py scan [--seconds 10] [--name C900]
  python tools/ble_survey.py gatt ADDR [--json out.json]
"""
import argparse
import asyncio
import json
import sys

# OTA / DFU services that must never be touched, not even read.
PROHIBITED = ("18a8", "ae10", "fe59", "00001530-1212-efde-1523-785feabcd123")


def mask(addr):
    a = str(addr)
    return a[:5] + "..." + a[-5:] if len(a) > 10 else "***"


def short(uuid):
    u = uuid.lower()
    if u.endswith("-0000-1000-8000-00805f9b34fb") and u.startswith("0000"):
        return "0x" + u[4:8].upper()
    return uuid.upper()


def prohibited(uuid):
    u = uuid.lower()
    return any(p in u for p in PROHIBITED)


async def scan(seconds, name):
    from bleak import BleakScanner
    found = await BleakScanner.discover(timeout=seconds, return_adv=True)
    rows = []
    for dev, adv in found.values():
        n = adv.local_name or dev.name or ""
        if name and name.lower() not in n.lower():
            continue
        rows.append((adv.rssi, n, dev.address, adv))
    for rssi, n, addr, adv in sorted(rows, key=lambda r: -r[0]):
        print(f"{rssi:5d} dBm  {n or '(no name)':24s}  id={addr}")
        if adv.service_uuids:
            print("        services: " + ", ".join(short(u) for u in adv.service_uuids))
        for cid, data in adv.manufacturer_data.items():
            print(f"        mfr 0x{cid:04X}: {data.hex()}")
    print(f"{len(rows)} device(s). The full id is printed so you can copy it; mask it before pasting.")


async def gatt(addr, out):
    from bleak import BleakClient
    report = {"address": mask(addr), "services": []}
    async with BleakClient(addr) as c:
        report["mtu"] = getattr(c, "mtu_size", None)
        for s in c.services:
            srow = {"uuid": short(s.uuid), "chars": []}
            report["services"].append(srow)
            blocked = prohibited(s.uuid)
            print(f"SERVICE {short(s.uuid)}{'  [PROHIBITED, not read]' if blocked else ''}")
            for ch in s.characteristics:
                crow = {"uuid": short(ch.uuid), "props": list(ch.properties)}
                line = f"  CHAR {short(ch.uuid)}  {','.join(ch.properties)}"
                if "read" in ch.properties and not blocked and not prohibited(ch.uuid):
                    try:
                        v = bytes(await c.read_gatt_char(ch))
                        crow["value_hex"] = v.hex()
                        txt = v.decode("ascii", "replace") if all(32 <= b < 127 for b in v) and v else ""
                        line += f"  = {v.hex()}" + (f"  '{txt}'" if txt else "")
                    except Exception as e:  # read refused is a result too
                        crow["read_error"] = str(e)
                        line += f"  read error: {e}"
                print(line)
                srow["chars"].append(crow)
    print(f"MTU: {report['mtu']}")
    if out:
        with open(out, "w") as f:
            json.dump(report, f, indent=2)
        print(f"wrote {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--seconds", type=float, default=10)
    s.add_argument("--name", default="")
    g = sub.add_parser("gatt")
    g.add_argument("address")
    g.add_argument("--json", default="")
    a = p.parse_args()
    try:
        import bleak  # noqa: F401
    except ImportError:
        sys.exit("bleak missing: pip install bleak")
    if a.cmd == "scan":
        asyncio.run(scan(a.seconds, a.name))
    else:
        asyncio.run(gatt(a.address, a.json))


if __name__ == "__main__":
    main()
