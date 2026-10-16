#!/usr/bin/env bash
# Idempotent cloud-box bootstrap for c900 Hiwear Plus rebuild.
# Usage (from repo root): bash tools/cloud_bootstrap.sh
# Env: CLOUD_TOOLS_DIR (default $HOME/tools), JADX_HEAP (default 3g), SKIP_APKTOOL=1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

JADX_VER=1.5.6
JADX_SHA=545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974
JADX_URL="https://github.com/skylot/jadx/releases/download/v${JADX_VER}/jadx-${JADX_VER}.zip"
APKTOOL_VER=3.0.3
APKTOOL_SHA=dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423
APKTOOL_URL="https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VER}/apktool_${APKTOOL_VER}.jar"
ZIP_REL=resources/c900/hiwear-plus-2.0.1.xapk.zip
ZIP_SHA=800662003d57aa272e5f829908c4c7671d1118ac4ed564242a5edcd4ca8e570e
INNER_SHA=5fa761a4d16ae8980fc40a341264441fe042858876ce1267dab54bd5be7b8952
TOOLS="${CLOUD_TOOLS_DIR:-$HOME/tools}"
HEAP="${JADX_HEAP:-3g}"
mkdir -p "$TOOLS/bin"
export PATH="$TOOLS/bin:$TOOLS/jadx/bin:$PATH"

need() { command -v "$1" >/dev/null 2>&1; }
sha_ok() { printf '%s  %s\n' "$1" "$2" | sha256sum -c - >/dev/null 2>&1; }
apt_install() {
  if need apt-get && need sudo; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@"
  elif need apt-get && [ "$(id -u)" -eq 0 ]; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@"
  else
    return 1
  fi
}

echo "cloud_bootstrap: root=$ROOT tools=$TOOLS"

# --- git-lfs ---
if ! need git-lfs; then
  apt_install git-lfs || { echo "FAIL: install git-lfs (apt install git-lfs)"; exit 1; }
fi
git lfs install --local >/dev/null 2>&1 || git lfs install >/dev/null 2>&1 || true

# --- JDK 17+ ---
java_ok() {
  need java || return 1
  java -version 2>&1 | head -1 | grep -qE 'version "(1[7-9]|[2-9][0-9])(\.|")'
}
if ! java_ok; then
  apt_install openjdk-17-jdk-headless \
    || apt_install openjdk-21-jdk-headless \
    || apt_install temurin-17-jdk \
    || { echo "FAIL: install OpenJDK 17+ (tried apt openjdk-17-jdk-headless and fallbacks)"; exit 1; }
fi
java_ok || { echo "FAIL: Java 17+ still missing"; exit 1; }

# --- unzip ---
need unzip || apt_install unzip || { echo "FAIL: need unzip"; exit 1; }

# --- jadx ---
jadx_ok() { need jadx && jadx --version 2>/dev/null | grep -q "$JADX_VER"; }
if ! jadx_ok; then
  tmp="$(mktemp -d)"
  cleanup_tmp() { rm -rf "$tmp"; }
  trap cleanup_tmp EXIT
  if ! curl -fsSL -A 'Mozilla/5.0' -o "$tmp/jadx.zip" "$JADX_URL"; then
    echo "FAIL: jadx download blocked ($JADX_URL)"
    exit 1
  fi
  sha_ok "$JADX_SHA" "$tmp/jadx.zip" || { echo "FAIL: jadx SHA-256 mismatch"; exit 1; }
  rm -rf "$TOOLS/jadx"
  mkdir -p "$TOOLS/jadx" "$tmp/out"
  unzip -q "$tmp/jadx.zip" -d "$tmp/out"
  if [ -x "$tmp/out/bin/jadx" ]; then
    cp -a "$tmp/out/." "$TOOLS/jadx/"
  else
    inner="$(find "$tmp/out" -type f -path '*/bin/jadx' | head -1)"
    [ -n "$inner" ] || { echo "FAIL: jadx zip layout unexpected"; exit 1; }
    cp -a "$(dirname "$(dirname "$inner")")/." "$TOOLS/jadx/"
  fi
  ln -sfn "$TOOLS/jadx/bin/jadx" "$TOOLS/bin/jadx"
  cleanup_tmp
  trap - EXIT
fi
jadx_ok || { echo "FAIL: jadx ${JADX_VER} not on PATH"; exit 1; }

# --- apktool (optional) ---
if [ "${SKIP_APKTOOL:-0}" != 1 ] && [ ! -f "$TOOLS/apktool/apktool.jar" ]; then
  mkdir -p "$TOOLS/apktool"
  if curl -fsSL -A 'Mozilla/5.0' -o "$TOOLS/apktool/apktool.jar" "$APKTOOL_URL"; then
    if sha_ok "$APKTOOL_SHA" "$TOOLS/apktool/apktool.jar"; then
      printf '%s\n' '#!/bin/sh' 'exec java -jar "$(dirname "$0")/apktool.jar" "$@"' >"$TOOLS/apktool/apktool"
      chmod +x "$TOOLS/apktool/apktool"
      ln -sfn "$TOOLS/apktool/apktool" "$TOOLS/bin/apktool"
    else
      rm -f "$TOOLS/apktool/apktool.jar"
      echo "note: apktool SHA-256 mismatch; removed (smali decode will need a retry)"
    fi
  else
    echo "note: apktool download skipped/blocked (ok for pure jadx recon)"
  fi
fi

# --- LFS: one archive ---
git lfs pull -I "$ZIP_REL"
if [ ! -f "$ZIP_REL" ]; then
  echo "FAIL: missing $ZIP_REL after git lfs pull"
  exit 1
fi
if head -c 120 "$ZIP_REL" | grep -q 'git-lfs.github.com'; then
  echo "FAIL: LFS pointer only (host blocked or quota); see docs/CLOUD-SETUP.md"
  exit 1
fi
sha_ok "$ZIP_SHA" "$ZIP_REL" || { echo "FAIL: zip SHA-256 mismatch"; exit 1; }

python3 - <<PY
import hashlib, sys, zipfile
zpath = "$ZIP_REL"
inner_expect = "$INNER_SHA"
with zipfile.ZipFile(zpath) as z:
    names = z.namelist()
    if len(names) != 1:
        print("FAIL: zip must hold exactly one member, got", names)
        sys.exit(1)
    h = hashlib.sha256(z.read(names[0])).hexdigest()
    if h != inner_expect:
        print("FAIL: inner XAPK SHA-256 mismatch", h)
        sys.exit(1)
print("inner xapk sha256 ok")
PY

# --- rebuild from REPO_COPY ---
python3 tools/rebuild_analysis.py c900 --max-heap "$HEAP"
test -f targets/c900/work/jadx.done
test -d targets/c900/decompiled/sources

echo PASS
