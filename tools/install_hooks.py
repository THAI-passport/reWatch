#!/usr/bin/env python3
"""Install a git pre-commit hook that runs `rw.py lint` (vendor artifacts, captures, emoji, secrets,
personal data) before every commit in this clone. Opt-in, per clone; agents and owners both run it once.

    python tools/install_hooks.py          # install (keeps an existing hook as pre-commit.bak)
    python tools/install_hooks.py --check  # exit 0 if installed
"""
import argparse
import os
import shutil
import stat
import subprocess
import sys

MARK = "# reWatch pre-commit (tools/install_hooks.py)"
HOOK = MARK + """
python3 tools/rw.py lint || python tools/rw.py lint || {
  echo "pre-commit: rw.py lint failed; fix it (personal data: skill re-privacy-scrub). Do not use --no-verify." >&2
  exit 1
}
"""


def hook_path(root):
    d = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    return os.path.join(root, d, "pre-commit")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = hook_path(root)
    present = os.path.isfile(p) and MARK in open(p, encoding="utf-8", errors="replace").read()
    if a.check:
        print("installed" if present else "not installed")
        return 0 if present else 1
    if present:
        print("already installed: %s" % p)
        return 0
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        shutil.copy2(p, p + ".bak")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("#!/bin/sh\n" + HOOK)
    os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("installed: %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
