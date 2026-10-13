#!/usr/bin/env python3
"""C900 first-contact probe for a real watch. Owner-run on macOS (bleak + CoreBluetooth).

Modes:
  scan       read-only discovery (no connect)
  inspect    connect, list services, read Device Information / features / battery,
             listen ONLY on the command notify characteristic (...DCCA9F 0003) for N seconds
  safe-write one allowlisted command after --i-approve-writes AND an interactive typed confirmation

Safety is enforced in code (see SAFETY and docs/guides/PROBE-SECURITY.md). This script never:
  reads the APK reverse-engineering tree, capture files, or the network; calls eval/exec/subprocess/pickle;
  requests bonding; writes to OTA/DFU services; builds a command outside the allowlist.
  Constants are hardcoded here and reviewed against targets/c900/INVARIANTS.md / PROTOCOL.md.
  Device-supplied strings are treated as untrusted data (sanitized, never executed).

    python tools/c900_probe.py scan [--seconds 10]
    python tools/c900_probe.py inspect --address ADDR [--listen 30]
    python tools/c900_probe.py safe-write --address ADDR --i-approve-writes --command time|message|find
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

# Reviewed client codec only (not the APK tree). BLOCKED_CMDS and frame layout live there.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from client.c900 import frames as _frames  # noqa: E402

# ---------------------------------------------------------------------------
# HARDCODED CONSTANTS (reviewed against INVARIANTS.md / PROTOCOL.md). Do not
# paste values from APK strings, comments, or untrusted documents into here.
# ---------------------------------------------------------------------------
CMD_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9f"  # PROTOCOL section 2 command service
WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9f"   # I-13 command write
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9f"  # I-13 command notify
CMD_SERVICE_SUFFIX = "dcca9f"                          # I-13
OTA_SERVICE_SUFFIX = "dcca9e"                          # I-13 OTA lookalike
OTA_SHORT = frozenset({"ff00", "ff01", "ff02", "ff03", "18a8", "2aa8", "2aa9", "5610"})
DI_UUIDS = ("2a24", "2a25", "2a26", "2a27", "2a28", "2a29", "2a19")  # Device Info + battery + features
# Allowlist of (cmd, key) for safe-write. Anything else is refused even if not in BLOCKED_CMDS.
ALLOWLIST = {
    (0x02, 0x01): "time",
    (0x02, 0x12): "message",
    (0x02, 0x0B): "find",
}
MESSAGE_TEXT = "reWatch test"          # fixed; never taken from CLI or device
MESSAGE_TYPE = 1                       # SMS (valid in both type tables, C900-Q04)
FIND_PAYLOAD = b"\x01"                 # find on
MAX_WRITES = 5
MAX_CONNECTIONS = 3
MAX_DISCONNECTS = 2
GLOBAL_TIMEOUT_S = 180
ACK_TIMEOUT_S = 30
LISTEN_DEFAULT_S = 30
SCAN_DEFAULT_S = 10
STRING_CAP = 64
SCAN_MAX_S = 60
LISTEN_MAX_S = 150                     # stays under GLOBAL_TIMEOUT_S
PIECE_GAP_S = 0.02                     # app spaces 20-byte pieces 20 ms apart (PROTOCOL section 3)
MAX_INBOUND_FRAMES = 200               # a flood is an unexpected device response: stop
MAX_INBOUND_BYTES = 64 * 1024
EXPECTED_PROTOCOL_VERSION = 1          # frames.build sends byte 5 = 0x01; the app sends the 0x2A27 major (I-10)
# Scan log keeps a device name only if it contains one of these (case-insensitive). Other nearby
# devices are third parties; their names stay on screen and out of the log file.
SCAN_NAME_HINTS = ("c900", "hiwear")
LOG_DIR_NAME = "captures"
# Bond-trigger inbound frames (I-30): log and stop; never act on them.
BOND_TRIGGERS = frozenset({(0x0C, 19), (0x0E, 1)})
EXIT_OK, EXIT_USAGE, EXIT_SAFETY, EXIT_DEVICE, EXIT_TIMEOUT = 0, 2, 3, 4, 5


class SafetyError(RuntimeError):
    """Raised when a hard safety rule fires; caller must disconnect and stop."""


# ---------------------------------------------------------------------------
# Sanitizers / redaction (device strings are untrusted)
# ---------------------------------------------------------------------------
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MAC_FULL = re.compile(r"(?i)\b([0-9a-f]{2}:){5}[0-9a-f]{2}\b")



def sanitize(value, cap=STRING_CAP):
    """Make a device-supplied string printable, length-capped, never a path/format/command."""
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        try:
            value = bytes(value).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            value = bytes(value).hex()
    s = _CTRL.sub("?", str(value))
    # C1 controls (0x80-0x9f, e.g. 8-bit CSI) and format chars (bidi overrides) can spoof terminal output.
    s = "".join("?" if (0x80 <= ord(c) <= 0x9F or unicodedata.category(c) == "Cf") else c for c in s)
    s = s.replace("%", "_").replace("{", "(").replace("}", ")")  # kill format/path tricks
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = re.sub(r"\.\.+[/\\]", "", s)
    if len(s) > cap:
        s = s[:cap] + "..."
    return s


def mask_mac(addr):
    a = str(addr or "")
    if len(a) == 17 and a.count(":") == 5:
        return a[:9] + "xx:xx:xx"
    if len(a) > 8:
        return a[:4] + "..." + a[-4:]
    return "???"


def redact_line(line):
    """Mask MACs and drop likely personal fields from a log line before writing."""
    s = _MAC_FULL.sub(lambda m: mask_mac(m.group(0)), str(line))
    # Never keep notification / caller / location style payloads in the log.
    for kw in ("message push", "caller", "location"):
        if kw in s.lower():
            idx = s.lower().find("payload")
            if idx != -1:
                s = s[:idx] + "payload=<redacted>"
            else:
                idx = s.lower().find(kw)
                s = s[:idx + len(kw)] + "=<redacted>"
            break
    return s


def is_ota_uuid(uuid):
    u = str(uuid or "").strip().lower()
    if u.endswith(OTA_SERVICE_SUFFIX):
        return True
    # Bluetrum "5610" DFU branding may appear in custom 128-bit UUIDs (Cus5610*). Fail closed.
    # Substring match is intentional; verified absent from command UUIDs ending ...dcca9f (I-13).
    if "5610" in u:
        return True
    short = u[4:8] if len(u) == 36 and u.startswith("0000") else (u if len(u) in (4, 8) else "")
    if len(u) == 8 and u.startswith("0000"):
        short = u[4:8]
    # expand short forms
    if len(u) == 4:
        short = u
    if short in OTA_SHORT or u in OTA_SHORT:
        return True
    # also match full bluetooth-base forms of the short list
    for s in OTA_SHORT:
        if u == ("0000%s-0000-1000-8000-00805f9b34fb" % s) or u.endswith(s):
            return True
    return u.endswith("dcca9e")


def norm_uuid(uuid):
    u = str(uuid or "").strip().lower()
    if len(u) == 4:
        return "0000%s-0000-1000-8000-00805f9b34fb" % u
    if len(u) == 8:
        return "%s-0000-1000-8000-00805f9b34fb" % u
    return u


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def check_log_dir(dest_dir):
    """A log dir must be <repo>/captures (git-ignored) or outside the repo, so a log is never committed by accident."""
    root = Path(dest_dir).expanduser().resolve() if dest_dir else (_ROOT / LOG_DIR_NAME).resolve()
    repo = _ROOT.resolve()
    caps = (repo / LOG_DIR_NAME).resolve()
    inside_repo = root == repo or repo in root.parents
    inside_caps = root == caps or caps in root.parents
    if inside_repo and not inside_caps:
        raise SafetyError("--log-dir inside the repo must be under %s/ (git-ignored)" % LOG_DIR_NAME)
    return root


class SessionLog:
    def __init__(self, mode, dest_dir=None):
        root = check_log_dir(dest_dir)
        root.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self._secrets = []
        for n in range(100):  # never overwrite an earlier log from the same second
            self.path = root / ("c900-probe-%s-%s%s.log" % (mode, stamp, "" if n == 0 else "-%d" % n))
            try:
                self._fp = open(self.path, "x", encoding="utf-8")
                break
            except FileExistsError:
                continue
        else:
            raise SafetyError("could not create a fresh log file")
        self.lines = []
        self.emit("PROBE_START mode=%s" % mode)

    def add_secret(self, value):
        """Mask this exact string (target MAC or CoreBluetooth UUID) wherever it appears, e.g. in bleak errors."""
        v = str(value or "")
        if len(v) >= 8 and v.lower() not in self._secrets:
            self._secrets.append(v.lower())

    def emit(self, msg):
        line = "%s %s" % (_dt.datetime.now().isoformat(timespec="seconds"), msg)
        for sec in self._secrets:
            line = re.sub(re.escape(sec), mask_mac(sec), line, flags=re.IGNORECASE)
        line = redact_line(line)
        self.lines.append(line)
        print(line, flush=True)
        self._fp.write(line + "\n")
        self._fp.flush()

    def close(self):
        self.emit("PROBE_END")
        self._fp.close()


# ---------------------------------------------------------------------------
# Session budget / abort state
# ---------------------------------------------------------------------------
class Budget:
    def __init__(self):
        self.writes = 0
        self.connections = 0
        self.disconnects = 0
        self.started = time.monotonic()
        self.abort_reason = None

    def check_time(self):
        if time.monotonic() - self.started > GLOBAL_TIMEOUT_S:
            raise SafetyError("global timeout %ds exceeded" % GLOBAL_TIMEOUT_S)

    def charge_connect(self):
        self.check_time()
        if self.connections >= MAX_CONNECTIONS:
            raise SafetyError("connection cap %d reached" % MAX_CONNECTIONS)
        self.connections += 1

    def note_disconnect(self):
        self.disconnects += 1
        if self.disconnects > MAX_DISCONNECTS:
            raise SafetyError("disconnect loop (>%d)" % MAX_DISCONNECTS)

    def charge_write(self):
        self.check_time()
        if self.writes >= MAX_WRITES:
            raise SafetyError("write cap %d reached" % MAX_WRITES)
        self.writes += 1


# ---------------------------------------------------------------------------
# Frame helpers (build only through allowlist)
# ---------------------------------------------------------------------------
def build_allowlisted(name, now=None):
    """Return (cmd, key, frame_bytes) for an allowlisted command name. Raises SafetyError otherwise."""
    name = str(name).lower().strip()
    if name == "time":
        now = now or _dt.datetime.now()
        payload = _frames.time_payload(now.year, now.month, now.day, now.hour, now.minute, now.second)
        cmd, key = 0x02, 0x01
    elif name == "message":
        payload = bytes([MESSAGE_TYPE, 0, 0]) + MESSAGE_TEXT.encode("utf-8")
        cmd, key = 0x02, 0x12
    elif name == "find":
        payload, cmd, key = FIND_PAYLOAD, 0x02, 0x0B
    else:
        raise SafetyError("command %r not in allowlist" % name)
    if (cmd, key) not in ALLOWLIST:
        raise SafetyError("internal: (%#x,%#x) missing from ALLOWLIST" % (cmd, key))
    if cmd in _frames.BLOCKED_CMDS:
        raise SafetyError("internal: cmd %#x is in BLOCKED_CMDS" % cmd)
    return cmd, key, _frames.build(cmd, key, payload)


def parse_inbound(data):
    """Parse one DF/FD frame. Returns dict; never raises on garbage (returns kind=bad)."""
    try:
        b = bytes(data)
        if len(b) < 9 or b[0] not in (_frames.APP_HEADER, _frames.ACK_HEADER):
            return {"kind": "bad", "hex": b[:32].hex()}
        if _frames.checksum(b) != b[3]:
            return {"kind": "bad-sum", "hex": b[:32].hex()}
        total = ((b[1] << 8) | b[2]) + 4
        if len(b) < total:
            return {"kind": "short", "hex": b[:32].hex()}
        if b[0] == _frames.ACK_HEADER:
            return {"kind": "ack", "cmd": b[4], "key": b[5], "status": b[8], "x": (b[6] << 8) | b[7]}
        plen = (b[7] << 8) | b[8]
        return {"kind": "cmd", "cmd": b[4], "key": b[6], "ver": b[5], "plen": plen,
                "payload_len": min(plen, max(0, len(b) - 9))}
    except Exception:  # noqa: BLE001
        return {"kind": "bad", "hex": bytes(data)[:32].hex()}


# ---------------------------------------------------------------------------
# BLE operations (bleak imported only at call time; injectable for tests)
# ---------------------------------------------------------------------------
_bleak_mod = None  # tests may set this


def _bleak():
    global _bleak_mod
    if _bleak_mod is not None:
        return _bleak_mod
    import bleak as _b  # local import keeps module importable without bleak for unit tests of pure helpers
    _bleak_mod = _b
    return _b


async def mode_scan(seconds, log):
    bleak = _bleak()
    log.emit("SCAN start seconds=%d (read-only, no connect)" % seconds)
    found = await bleak.BleakScanner.discover(timeout=float(seconds), return_adv=True)
    rows = []
    for addr, (dev, adv) in found.items() if isinstance(found, dict) else []:
        name = sanitize(getattr(dev, "name", None) or getattr(adv, "local_name", None) or "")
        rssi = getattr(adv, "rssi", None)
        md = getattr(adv, "manufacturer_data", {}) or {}
        md_hex = " ".join("%04x:%s" % (k, sanitize(bytes(v).hex(), 48)) for k, v in sorted(md.items()))
        row = {"address": mask_mac(addr), "address_full_for_owner_only": str(addr),
               "name": name, "rssi": rssi, "manufacturer": md_hex}
        rows.append(row)
        log.add_secret(addr)
        log.emit("SCAN device name=%s rssi=%s mac=%s mfg=%s" % (scan_log_name(name), rssi, mask_mac(addr), mask_mfg(md)))
    # Print a selection helper (full address only to stdout for the owner; log stays masked).
    # Screen only (not the log file): full address, every name, full manufacturer bytes. Do not tee this.
    print("--- screen only, not logged: select with --address <full address> ---", flush=True)
    for r in rows:
        print("  %s  rssi=%s  name=%r  mfg=%s" % (r["address_full_for_owner_only"], r["rssi"], r["name"],
                                                r["manufacturer"]), flush=True)
    log.emit("SCAN done count=%d" % len(rows))
    return rows


def scan_log_name(name):
    """Name for the log file: kept for likely C900 candidates, redacted for third-party devices."""
    if any(h in name.lower() for h in SCAN_NAME_HINTS):
        return repr(name)
    return "<redacted len=%d>" % len(name) if name else "''"


def mask_mfg(md):
    """Manufacturer data for the log: company id, length, first 2 bytes. The C900 record may carry its
    own MAC (PROTOCOL section 3: MAC followed by 12 34), so the rest never goes into the file."""
    out = []
    for k, v in sorted((md or {}).items()):
        b = bytes(v)
        out.append("%04x:len=%d:%s%s" % (int(k) & 0xFFFF, len(b), b[:2].hex(), ".." if len(b) > 2 else ""))
    return " ".join(out)


def pair_state(client):
    """True/False if the BLE stack exposes bond state, None if it does not (bleak 3.0.2 has no
    BleakClient.is_paired; CoreBluetooth has no bond-state API at all). Never raises."""
    try:
        v = getattr(client, "is_paired")
    except Exception:  # noqa: BLE001  (AttributeError, NotImplementedError, backend errors)
        return None
    return v if isinstance(v, bool) else None


def protocol_major(raw):
    """Integer major from a 0x2A27 value the way the app reads it: strip a leading V/v, take digits
    before the first dot (PROTOCOL section 4). None if it cannot be read."""
    s = bytes(raw or b"").decode("ascii", "replace").strip()
    if s[:1] in ("V", "v"):
        s = s[1:]
    m = re.match(r"(\d{1,3})(?:\.|$)", s)
    return int(m.group(1)) if m else None


def command_chars(services):
    """Return (write_char, notify_char) objects from the command service itself. Writes and the CCCD
    write go to these objects, never to a bare UUID string, so a duplicate UUID elsewhere (for example
    under an OTA service) can never be the target. Raises SafetyError if not exactly one of each."""
    _require_command_layout(services)
    writes, notifies = [], []
    for svc in services:
        if norm_uuid(getattr(svc, "uuid", "")) != CMD_SERVICE_UUID:
            continue
        for ch in getattr(svc, "characteristics", []) or []:
            cu = norm_uuid(ch.uuid)
            if cu == WRITE_UUID:
                writes.append(ch)
            elif cu == NOTIFY_UUID:
                notifies.append(ch)
    if len(writes) != 1 or len(notifies) != 1:
        raise SafetyError("command service must hold exactly one write and one notify (found %d/%d)"
                          % (len(writes), len(notifies)))
    return writes[0], notifies[0]


class FrameReader:
    """Reassemble DF/FD frames from notifications with resync and hard caps. Used by both modes."""

    def __init__(self):
        self.buf = bytearray()
        self.frames = 0
        self.bytes = 0

    def feed(self, data):
        self.bytes += len(data)
        if self.bytes > MAX_INBOUND_BYTES:
            raise SafetyError("inbound flood: more than %d bytes" % MAX_INBOUND_BYTES)
        self.buf.extend(data)
        out = []
        while self.buf:
            while self.buf and self.buf[0] not in (_frames.APP_HEADER, _frames.ACK_HEADER):
                del self.buf[0]
            if len(self.buf) < 3:
                break
            total = ((self.buf[1] << 8) | self.buf[2]) + 4
            if total < 9 or total > 1024:
                del self.buf[0]
                continue
            if len(self.buf) < total:
                break
            frame = bytes(self.buf[:total])
            del self.buf[:total]
            self.frames += 1
            if self.frames > MAX_INBOUND_FRAMES:
                raise SafetyError("inbound flood: more than %d frames" % MAX_INBOUND_FRAMES)
            out.append(parse_inbound(frame))
        return out


def _require_command_layout(services):
    """Validate GATT layout. OTA services may be present but must not be used. Raises SafetyError."""
    have_write = have_notify = False
    ota_present = []
    for svc in services:
        su = norm_uuid(getattr(svc, "uuid", ""))
        is_ota_svc = is_ota_uuid(su) or su.endswith(OTA_SERVICE_SUFFIX)
        if is_ota_svc:
            ota_present.append(su)
        for ch in getattr(svc, "characteristics", []) or []:
            cu = norm_uuid(ch.uuid)
            if is_ota_uuid(cu) or cu.endswith(OTA_SERVICE_SUFFIX):
                ota_present.append(cu)
            # Hard refuse: write char under OTA service or matching OTA write / lookalike
            if is_ota_svc and cu in (WRITE_UUID, NOTIFY_UUID):
                raise SafetyError("refusing: command characteristic on OTA service %s/%s" % (su, cu))
            if cu.startswith("6e400002") and cu.endswith(OTA_SERVICE_SUFFIX):
                raise SafetyError("refusing: write characteristic on OTA service %s" % cu)
            if not is_ota_svc:
                if cu == WRITE_UUID and ("write" in ch.properties or "write-without-response" in ch.properties):
                    have_write = True
                if cu == NOTIFY_UUID and ("notify" in ch.properties or "indicate" in ch.properties):
                    have_notify = True
    if not (have_write and have_notify):
        raise SafetyError("unexpected service layout: missing command write/notify (...DCCA9F 0002/0003)")
    return ota_present


async def _write_cmd_piece(client, piece, write_char):
    """Single ATT write to the command write characteristic object; OTA refused."""
    if is_ota_uuid(WRITE_UUID) or not WRITE_UUID.endswith(CMD_SERVICE_SUFFIX):
        raise SafetyError("refusing write: WRITE_UUID is not the command characteristic")
    if norm_uuid(getattr(write_char, "uuid", "")) != WRITE_UUID:
        raise SafetyError("refusing write to non-command characteristic")
    # App writes without response (PROTOCOL section 2); fall back to with-response only if the
    # characteristic does not offer it (CoreBluetooth drops a disallowed write type silently).
    props = getattr(write_char, "properties", []) or []
    await client.write_gatt_char(write_char, piece, response="write-without-response" not in props)


async def _safe_disconnect(client, log):
    try:
        if getattr(client, "is_connected", False):
            await client.disconnect()
            log.emit("DISCONNECT ok")
    except Exception as e:  # noqa: BLE001
        log.emit("DISCONNECT error=%s" % sanitize(str(e), 80))


async def mode_inspect(address, listen_s, log, budget, name_filter=None):
    bleak = _bleak()
    address = await _resolve_target(address, name_filter, log)
    log.add_secret(address)
    budget.charge_connect()
    log.emit("INSPECT connect mac=%s listen=%ds" % (mask_mac(address), listen_s))
    client = bleak.BleakClient(address, timeout=20.0)
    abort = {"reason": None}
    reader = FrameReader()
    inbound = []

    def on_notify(_handle, data):
        if abort["reason"]:
            return
        try:
            for info in reader.feed(data):
                inbound.append(info)
                if info["kind"] == "cmd" and (info["cmd"], info["key"]) in BOND_TRIGGERS:
                    abort["reason"] = "bond-trigger inbound cmd=0x%02x key=%d" % (info["cmd"], info["key"])
                    log.emit("ABORT %s" % abort["reason"])
                    return
                if info["kind"] == "ack":
                    log.emit("RX ack cmd=0x%02x key=%d status=%d" % (info["cmd"], info["key"], info["status"]))
                elif info["kind"] == "cmd":
                    log.emit("RX cmd=0x%02x key=%d plen=%d" % (info["cmd"], info["key"], info.get("plen", 0)))
                else:
                    log.emit("RX %s" % info.get("kind"))
        except Exception as e:  # noqa: BLE001  (SafetyError on flood included)
            abort["reason"] = "notify handler: %s" % sanitize(str(e), 60)

    try:
        await client.connect()
        if not client.is_connected:
            raise SafetyError("connect failed")
        # Never call client.pair(). If already paired, note it; if pairing state flips, abort.
        paired_before = pair_state(client)
        if paired_before is None:
            log.emit("NOTE pairing detection unavailable on this BLE stack; if the OS shows a pairing "
                     "dialog press Cancel, then Ctrl-C")
        elif paired_before:
            log.emit("NOTE device reports already paired; probe will not request bonding")
        write_char, notify_char = command_chars(client.services)
        ota = _require_command_layout(client.services)
        log.emit("LAYOUT ok command-service present; ota_services_seen=%d (untouched)" % len(ota))
        for svc in client.services:
            su = sanitize(norm_uuid(svc.uuid), 40)
            chars = []
            for ch in svc.characteristics:
                chars.append("%s[%s]" % (sanitize(norm_uuid(ch.uuid), 40), ",".join(ch.properties)))
            log.emit("SERVICE %s chars=%s" % (su, sanitize(";".join(chars), 200)))
        # Reads: Device Information + features + battery. Never write here.
        for short in DI_UUIDS:
            u = norm_uuid(short)
            try:
                raw = bytes(await client.read_gatt_char(u))
            except Exception as e:  # noqa: BLE001
                log.emit("READ %s error=%s" % (short, sanitize(str(e), 60)))
                continue
            if short == "2a19" and raw:
                log.emit("READ battery=%d%%" % (raw[0] & 0xFF))
            elif short == "2a28":
                marker = raw[0] if raw else None
                bits = {}
                if len(raw) > 1:
                    bits["isBLE3"] = bool(raw[1] & 0x80)
                if len(raw) > 15:
                    bits["isSupportPair"] = bool(raw[15] & 0x40)
                if len(raw) > 25:
                    bits["hideHrAndDnd"] = bool(raw[25] & 0x80)
                log.emit("READ features marker=%s len=%d bits=%s hex=%s" % (
                    hex(marker) if marker is not None else None, len(raw), bits, raw[:64].hex()))
            elif short == "2a25":
                # Standard meaning is Serial Number; the app calls it "platform". Treat as personal.
                log.emit("READ 2a25 value=<redacted len=%d>" % len(raw))
            elif short == "2a27":
                log.emit("READ 2a27 value=%s protocol_major=%s" % (sanitize(raw, 48), protocol_major(raw)))
            else:
                log.emit("READ %s value=%s" % (short, sanitize(raw, 48)))
        # Listen ONLY on command notify. Refuse if that UUID is somehow OTA.
        if is_ota_uuid(NOTIFY_UUID) or not NOTIFY_UUID.endswith(CMD_SERVICE_SUFFIX):
            raise SafetyError("internal: NOTIFY_UUID is not the command characteristic")
        await client.start_notify(notify_char, on_notify)
        log.emit("LISTEN start uuid=...%s seconds=%d (CCCD write is the only write)" % (NOTIFY_UUID[-12:], listen_s))
        end = time.monotonic() + float(listen_s)
        while time.monotonic() < end:
            budget.check_time()
            if abort["reason"]:
                raise SafetyError(abort["reason"])
            if not client.is_connected:
                budget.note_disconnect()
                raise SafetyError("unexpected disconnect during listen")
            # Pairing detection (only where the stack exposes it): a flip after connect stops the probe.
            if paired_before is False and pair_state(client):
                raise SafetyError("pairing/bonding detected (probe never requests this)")
            await asyncio.sleep(0.2)
        if abort["reason"]:
            raise SafetyError(abort["reason"])
        try:
            await client.stop_notify(notify_char)
        except Exception:  # noqa: BLE001
            pass
        log.emit("LISTEN done frames=%d" % len(inbound))
        return {"inbound": inbound, "ota_seen": len(ota)}
    finally:
        await _safe_disconnect(client, log)


async def _resolve_target(address, name_filter, log):
    if address:
        return str(address)
    if not name_filter:
        raise SafetyError("target required: pass --address or --name (never auto-picks the first device)")
    bleak = _bleak()
    found = await bleak.BleakScanner.discover(timeout=float(SCAN_DEFAULT_S), return_adv=True)
    matches = []
    items = found.items() if isinstance(found, dict) else []
    for addr, (dev, adv) in items:
        name = getattr(dev, "name", None) or getattr(adv, "local_name", None) or ""
        if name == name_filter:  # exact match only
            matches.append(addr)
    if len(matches) != 1:
        raise SafetyError("exact --name %r matched %d device(s); use --address instead" % (name_filter, len(matches)))
    log.emit("TARGET resolved name=%r -> mac=%s" % (sanitize(name_filter), mask_mac(matches[0])))
    return matches[0]


async def mode_safe_write(address, command, log, budget, approve, confirm_fn, name_filter=None):
    if not approve:
        raise SafetyError("refusing: --i-approve-writes is required for safe-write")
    cmd, key, frame = build_allowlisted(command)
    # Interactive confirmation: owner must type the command name again.
    prompt = ("Type the command name %r to confirm sending ONE allowlisted frame "
              "(cmd=0x%02x key=0x%02x, %d bytes), or anything else to abort: " % (command, cmd, key, len(frame)))
    answer = confirm_fn(prompt)
    if str(answer).strip().lower() != command.lower():
        raise SafetyError("confirmation mismatch; nothing sent")
    bleak = _bleak()
    address = await _resolve_target(address, name_filter, log)
    log.add_secret(address)
    budget.charge_connect()
    log.emit("SAFE_WRITE connect mac=%s command=%s" % (mask_mac(address), command))
    client = bleak.BleakClient(address, timeout=20.0)
    # armed flips only after the first byte is on the air, so an ack that arrived earlier
    # (unsolicited or stale) can never be taken as the answer to this write.
    ack_box = {"ack": None, "abort": None, "armed": False}
    reader = FrameReader()
    notify_char = None

    def on_notify(_h, data):
        if ack_box["abort"]:
            return
        try:
            for info in reader.feed(data):
                if info["kind"] == "cmd" and (info["cmd"], info["key"]) in BOND_TRIGGERS:
                    ack_box["abort"] = "bond-trigger inbound cmd=0x%02x key=%d" % (info["cmd"], info["key"])
                    return
                if info["kind"] == "ack" and ack_box["armed"] and ack_box["ack"] is None:
                    ack_box["ack"] = info
        except Exception as e:  # noqa: BLE001  (SafetyError on flood included)
            ack_box["abort"] = "notify handler: %s" % sanitize(str(e), 60)

    try:
        await client.connect()
        if not client.is_connected:
            raise SafetyError("connect failed")
        paired_before = pair_state(client)
        if paired_before is None:
            log.emit("NOTE pairing detection unavailable on this BLE stack; if the OS shows a pairing "
                     "dialog press Cancel, then Ctrl-C")
        elif paired_before:
            # Already paired is OK (owner may have paired earlier); we still never call pair().
            log.emit("NOTE already paired; probe will not request bonding")
        write_char, notify_char = command_chars(client.services)
        if is_ota_uuid(WRITE_UUID) or not WRITE_UUID.endswith(CMD_SERVICE_SUFFIX):
            raise SafetyError("internal: WRITE_UUID is not the command characteristic")
        # Byte 5 of our frame is 0x01; the app puts the 0x2A27 major there (I-10). Never send a frame
        # the app would not send: refuse unless the watch reports major 1.
        try:
            hw = bytes(await client.read_gatt_char(norm_uuid("2a27")))
        except Exception as e:  # noqa: BLE001
            raise SafetyError("cannot read 0x2A27 to check protocol version: %s" % sanitize(str(e), 60))
        major = protocol_major(hw)
        log.emit("READ 2a27 value=%s protocol_major=%s" % (sanitize(hw, 48), major))
        if major != EXPECTED_PROTOCOL_VERSION:
            raise SafetyError("protocol version %s != %d; frame would differ from the app's; nothing sent"
                              % (major, EXPECTED_PROTOCOL_VERSION))
        # Subscribe so we can see the ack. CCCD write only on command notify.
        await client.start_notify(notify_char, on_notify)
        # Chunk into 20-byte ATT pieces (I-16).
        pieces = [frame[i:i + 20] for i in range(0, len(frame), 20)]
        if budget.writes + len(pieces) > MAX_WRITES:
            raise SafetyError("refusing write: %d piece(s) exceeds remaining write cap (%d/%d)" %
                              (len(pieces), budget.writes, MAX_WRITES))
        if ack_box["abort"]:
            raise SafetyError(ack_box["abort"])
        ack_box["ack"] = None
        ack_box["armed"] = True
        for i, piece in enumerate(pieces):
            if i:
                await asyncio.sleep(PIECE_GAP_S)
            budget.charge_write()
            await _write_cmd_piece(client, piece, write_char)
            log.emit("TX piece %d/%d len=%d" % (i + 1, len(pieces), len(piece)))
        # Wait for ack matching cmd/key.
        end = time.monotonic() + ACK_TIMEOUT_S
        while time.monotonic() < end:
            budget.check_time()
            if ack_box["abort"]:
                raise SafetyError(ack_box["abort"])
            if not client.is_connected:
                budget.note_disconnect()
                raise SafetyError("disconnect while waiting for ack")
            # Pairing detection (only where the stack exposes it).
            if paired_before is False and pair_state(client):
                raise SafetyError("pairing/bonding detected (probe never requests this)")
            a = ack_box["ack"]
            if a is not None:
                if a["cmd"] != cmd or a["key"] != key:
                    raise SafetyError("unexpected ack cmd=0x%02x key=%d" % (a["cmd"], a["key"]))
                if a["status"] != 1:
                    raise SafetyError("ack status=%d (not ok); stopping" % a["status"])
                log.emit("ACK ok cmd=0x%02x key=0x%02x status=1 x=0x%04x" % (cmd, key, a.get("x", 0)))
                return a
            await asyncio.sleep(0.1)
        raise SafetyError("ack timeout after %ds" % ACK_TIMEOUT_S)
    finally:
        if notify_char is not None:
            try:
                await client.stop_notify(notify_char)
            except Exception:  # noqa: BLE001
                pass
        await _safe_disconnect(client, log)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _confirm_tty(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ""


def _bounded(hi):
    def conv(text):
        v = float(text)
        if not (0 < v <= hi):  # also rejects nan
            raise argparse.ArgumentTypeError("must be > 0 and <= %s seconds" % hi)
        return v
    return conv


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("scan", help="read-only scan")
    p.add_argument("--seconds", type=_bounded(SCAN_MAX_S), default=SCAN_DEFAULT_S)
    p.add_argument("--log-dir")
    p = sub.add_parser("inspect", help="connect, read, listen on command notify only")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--address")
    g.add_argument("--name", help="exact local-name match (alternative to --address)")
    p.add_argument("--listen", type=_bounded(LISTEN_MAX_S), default=LISTEN_DEFAULT_S)
    p.add_argument("--log-dir")
    p = sub.add_parser("safe-write", help="one allowlisted write after dual approval")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--address")
    g.add_argument("--name", help="exact local-name match (alternative to --address)")
    p.add_argument("--command", required=True, choices=sorted(set(ALLOWLIST.values())))
    p.add_argument("--i-approve-writes", action="store_true")
    p.add_argument("--log-dir")
    return ap


async def _amain(args, confirm_fn=_confirm_tty):
    log = SessionLog(args.mode, getattr(args, "log_dir", None))
    budget = Budget()
    # Ctrl-C -> disconnect path via CancelledError in the finally of each mode.
    try:
        if args.mode == "scan":
            await asyncio.wait_for(mode_scan(args.seconds, log), timeout=GLOBAL_TIMEOUT_S)
            return EXIT_OK
        if not getattr(args, "address", None) and not getattr(args, "name", None):
            raise SafetyError("target required: pass --address or --name")
        if args.mode == "inspect":
            await asyncio.wait_for(mode_inspect(args.address, args.listen, log, budget, args.name),
                                   timeout=GLOBAL_TIMEOUT_S)
            return EXIT_OK
        if args.mode == "safe-write":
            await asyncio.wait_for(
                mode_safe_write(args.address, args.command, log, budget, args.i_approve_writes, confirm_fn, args.name),
                timeout=GLOBAL_TIMEOUT_S)
            return EXIT_OK
        raise SafetyError("unknown mode")
    except SafetyError as e:
        log.emit("SAFETY_STOP %s" % sanitize(str(e), 120))
        return EXIT_SAFETY
    except asyncio.TimeoutError:
        log.emit("SAFETY_STOP global timeout")
        return EXIT_TIMEOUT
    except asyncio.CancelledError:
        log.emit("SAFETY_STOP cancelled")
        raise
    except Exception as e:  # noqa: BLE001
        log.emit("ERROR %s" % sanitize(str(e), 120))
        return EXIT_DEVICE
    finally:
        log.close()
        print("log: %s" % log.path, flush=True)


def main(argv=None, confirm_fn=_confirm_tty):
    args = build_parser().parse_args(argv)
    try:
        check_log_dir(getattr(args, "log_dir", None))
    except SafetyError as e:
        print("error: %s" % e, file=sys.stderr)
        return EXIT_USAGE
    try:
        return asyncio.run(_amain(args, confirm_fn=confirm_fn))
    except KeyboardInterrupt:
        print("interrupted; disconnect requested", file=sys.stderr)
        return EXIT_SAFETY


if __name__ == "__main__":
    sys.exit(main())
