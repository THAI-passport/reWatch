#!/usr/bin/env python3
"""Read the pinned companion APK without jadx: list strings, find classes/methods, dump one method's
bytecode, list callers of a method. For agents on machines where jadx/apktool cannot be installed.

Needs androguard (`pip install -r requirements-static.txt`, in a venv). Input is the base APK (or a
.dex). Output is text for the agent to read; never commit it (it is decompiled vendor code).

    python tools/dexgrep.py APK strings REGEX            # string table matches (dex file, string)
    python tools/dexgrep.py APK classes REGEX            # class names
    python tools/dexgrep.py APK methods CLASS_REGEX      # methods of matching classes
    python tools/dexgrep.py APK dump CLASS_REGEX METHOD  # bytecode of matching methods
    python tools/dexgrep.py APK refs REGEX               # methods whose bytecode text matches REGEX
    python tools/dexgrep.py APK manifest                 # AndroidManifest.xml (permissions, services)

Get the base APK from the pinned LFS copy:
    git lfs pull -I resources/c900/hiwear-plus-2.0.1.xapk.zip
    python tools/dexgrep.py --extract resources/c900/hiwear-plus-2.0.1.xapk.zip work/c900-apk
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import zipfile


def _need():
    try:
        from androguard.core.dex import DEX  # noqa: F401
        return DEX
    except Exception:  # noqa: BLE001
        sys.exit("androguard missing: python -m pip install -r requirements-static.txt (inside a venv)")


def extract(xapk_zip, out_dir):
    """Unpack outer zip -> inner .xapk -> base APK; print its SHA-256 for comparison with SOURCES.md."""
    import hashlib
    os.makedirs(out_dir, exist_ok=True)
    z = zipfile.ZipFile(xapk_zip)
    inner = zipfile.ZipFile(io.BytesIO(z.read(z.namelist()[0])))
    for n in inner.namelist():
        if n.endswith(".apk"):
            p = os.path.join(out_dir, os.path.basename(n))
            with open(p, "wb") as f:
                f.write(inner.read(n))
    for f in sorted(os.listdir(out_dir)):
        if f.endswith(".apk"):
            h = hashlib.sha256(open(os.path.join(out_dir, f), "rb").read()).hexdigest()
            print("%s  %s" % (h, f))


def load_dex(path):
    DEX = _need()
    if path.endswith(".dex"):
        return [(os.path.basename(path), DEX(open(path, "rb").read()))]
    z = zipfile.ZipFile(path)
    return [(n, DEX(z.read(n))) for n in sorted(z.namelist()) if re.match(r"classes\d*\.dex$", n)]


def method_text(m):
    code = m.get_code()
    if not code:
        return ""
    return "\n".join("%s %s" % (i.get_name(), i.get_output()) for i in code.get_bc().get_instructions())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", nargs=2, metavar=("XAPK_ZIP", "OUT_DIR"))
    ap.add_argument("apk", nargs="?")
    ap.add_argument("cmd", nargs="?", choices=["strings", "classes", "methods", "dump", "refs", "manifest"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--limit", type=int, default=200)
    a = ap.parse_args(argv)
    if a.extract:
        extract(*a.extract)
        return 0
    if not a.apk or not a.cmd:
        ap.error("APK and command required")
    if a.cmd == "manifest":
        _need()
        from androguard.core.apk import APK
        print(APK(a.apk).get_android_manifest_axml().get_xml().decode("utf-8", "replace"))
        return 0
    rx = re.compile(a.args[0], re.I) if a.args else re.compile(".")
    n = 0
    for name, d in load_dex(a.apk):
        if a.cmd == "strings":
            for s in d.get_strings():
                if rx.search(s):
                    print("%s\t%s" % (name, s.replace("\n", "\\n")[:300])); n += 1
        else:
            for c in d.get_classes():
                cn = c.get_name()
                if a.cmd == "classes":
                    if rx.search(cn):
                        print("%s\t%s\tsuper=%s" % (name, cn, c.get_superclassname())); n += 1
                    continue
                if a.cmd in ("methods", "dump") and not rx.search(cn):
                    continue
                for m in c.get_methods():
                    if a.cmd == "methods":
                        print("%s\t%s->%s%s" % (name, cn, m.get_name(), m.get_descriptor())); n += 1
                    elif a.cmd == "dump" and (len(a.args) < 2 or m.get_name() == a.args[1]):
                        print("##### %s->%s%s\n%s" % (cn, m.get_name(), m.get_descriptor(), method_text(m))); n += 1
                    elif a.cmd == "refs" and rx.search(method_text(m)):
                        print("%s\t%s->%s" % (name, cn, m.get_name())); n += 1
                    if n >= a.limit:
                        break
                if n >= a.limit:
                    break
        if n >= a.limit:
            print("... stopped at --limit %d" % a.limit)
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
