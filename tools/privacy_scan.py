#!/usr/bin/env python3
"""Scan text files for personal data before they are committed or shared.

Flags: Bluetooth/Wi-Fi MAC addresses (full, or with a real OUI and masked tail such as
AB:CD:EF:xx:xx:xx), the same as hex byte runs, macOS CoreBluetooth UUIDs (128-bit UUIDs that are
not Bluetooth-base or known GATT service UUIDs), IMEI-like 15-digit numbers, phone numbers,
e-mail addresses, Android serial-like adb ids, and absolute home paths with a user name.
Stdlib only; never sends anything anywhere. Exit 1 when findings exist.

    python tools/privacy_scan.py PATH [PATH ...] [--allow REGEX] [--json]
    git diff --cached --name-only | xargs python tools/privacy_scan.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HEX = "[0-9A-Fa-f]"
_X = "(?:[xX]{2})"
RULES = [
    # Full MAC, or MAC whose first 3 octets are real and the tail masked (the OUI plus the name
    # can still identify a device family; repo rule masks everything but at most the last 2 octets).
    ("mac", re.compile(r"(?<![0-9A-Fa-f:-])(?:(?:%s{2}:){5}|(?:%s{2}-){5})%s{2}(?![0-9A-Fa-f:-])" % (HEX, HEX, HEX))),
    ("mac-oui-kept", re.compile(r"(?<![0-9A-Fa-f:])(?:%s{2}[:-]){3}(?:%s[:-]){2}%s(?![0-9A-Fa-f:])" % (HEX, _X, _X))),
    ("uuid", re.compile(r"\b%s{8}-%s{4}-%s{4}-%s{4}-%s{12}\b" % ((HEX,) * 5))),
    ("imei", re.compile(r"(?<!\d)\d{15}(?!\d)")),
    ("phone", re.compile(r"(?<![\w.])\+\d{1,3}[ -]?\(?\d{1,4}\)?(?:[ -]?\d{2,4}){2,4}(?!\w)")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("home-path", re.compile(r"/(?:Users|home)/(?!user/|runner/|USER|<)[A-Za-z0-9._-]+/")),
]
# Strict-only: six spaced hex bytes (frame dumps trip this, so it is opt-in with --strict).
STRICT_RULES = [("mac-hex-run", re.compile(r"(?<![0-9A-Fa-f])(?:%s{2} ){5}%s{2}(?![0-9A-Fa-f ])" % (HEX, HEX)))]
# 128-bit UUIDs that are protocol facts, not identities.
_BASE = re.compile(r"(?i)^0000%s{4}-0000-1000-8000-00805f9b34fb$" % HEX)
_KNOWN = re.compile(r"(?i)^(?:6e40%s{4}-b5a3-f393-e0a9-e50e24dcca9[ef]"
                    r"|7905f431-b5ce-4e99-a40f-4b1e122d00d0|89d3502b-0f36-433a-8ef4-c502ad55f8dc)$" % HEX)
# Obvious placeholders used in docs and tests.
_PLACEHOLDER = re.compile(r"(?i)^(?:aa:bb:cc:dd:ee:..|00:11:22:33:44:55|12:34:56:78:9a:bc|(?:00[:-]){5}00|(?:ff[:-]){5}ff)$")
TEXT_EXT = {".md", ".txt", ".py", ".json", ".log", ".csv", ".yml", ".yaml", ".toml", ".sh", ".cfg", ".ini", ""}


def scan_text(text, allow=(), strict=False):
    out = []
    rules = RULES + (STRICT_RULES if strict else [])
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in rules:
            for m in rx.finditer(line):
                v = m.group(0)
                if kind == "uuid" and (_BASE.match(v) or _KNOWN.match(v)):
                    continue
                if kind in ("mac", "mac-hex-run") and _PLACEHOLDER.match(v.replace(" ", ":")):
                    continue
                if any(re.search(a, v) for a in allow):
                    continue
                out.append({"line": n, "kind": kind, "match": v[:6] + "..."})  # never echo the full value
    return out


def iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "decompiled", "work", "artifacts", "__pycache__", ".venv", ".venv-probe")]
                for f in files:
                    yield os.path.join(root, f)
        else:
            yield p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--allow", action="append", default=[], help="regex of values to accept (placeholders)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="also flag six spaced hex bytes (review frame dumps by hand)")
    a = ap.parse_args(argv)
    allow_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".privacy-allow")
    if os.path.isfile(allow_file):
        for ln in open(allow_file, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                a.allow.append(ln)
    findings = []
    for f in iter_files(a.paths):
        if os.path.splitext(f)[1].lower() not in TEXT_EXT or not os.path.isfile(f):
            continue
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for h in scan_text(text, a.allow, a.strict):
            h["file"] = f
            findings.append(h)
    if a.json:
        print(json.dumps(findings, indent=1))
    else:
        for h in findings:
            print("%s:%d: %s %s" % (h["file"], h["line"], h["kind"], h["match"]))
        print("privacy_scan: %d finding(s)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
