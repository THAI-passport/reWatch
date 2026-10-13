#!/usr/bin/env python3
"""Decode C900 / Hiwear Plus DF/FD command frames from a Bluetooth capture (decode only; stdlib only).

    python tools/c900_decode.py capture.btsnoop|.pcap|.pcapng|btcap.json [--json out.json] [--show-text]
        [--write-uuid U | --write-handle H] [--notify-uuid U | --notify-handle H]

It never connects, sends, replays or writes anything: input is a file, output is text/JSON.
Steps: ATT rows from tools/btcap.py (capture) or its --json output; keep the command write and notify characteristics
(default `6e400002-...dcca9f` / `6e400003-...dcca9f`, PROTOCOL §2); reassemble DF/FD frames to len + 4 bytes per
direction; check the sum (PROTOCOL §4); label cmd/key from PROTOCOL §5/§7 names; flag blocked cmds (INVARIANTS I-20)
and any traffic on OTA characteristics. From a capture file (not JSON) it also pairs ATT reads to show 0x2A27/0x2A26/0x2A28/0x2A19
and decodes feature bits. Privacy: message text, caller, user name, profile and location payloads (cmd 2 keys 18/17/36/4, 0x1A 23/24) and MACs (0x0E key 1) are hidden unless --show-text / masked always.
Labels are names already in PROTOCOL.md, not new claims; a decoded capture value is [H] only once written to a result file.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import btcap  # noqa: E402

DF, FD = 0xDF, 0xFD
WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9f"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9f"
BLOCKED = {0x01: "OTA", 0x04: "UNBIND", 0x06: "RESET", 0x07: "FACTORY_TEST", 0x0D: "RESTORE", 0x13: "OTA_NEW"}
OTA_UUIDS = {"ff00", "ff01", "ff02", "ff03", "18a8", "2aa8", "2aa9"}

CMD = {0x01: "OTA (old)", 0x02: "settings", 0x03: "bind", 0x04: "unbind", 0x05: "health/sport data", 0x06: "reset",
       0x07: "factory test", 0x08: "alarm list", 0x09: "settings query/reply", 0x0A: "flash read", 0x0B: "device test",
       0x0C: "device control", 0x0E: "BT 3.0 info", 0x0F: "watch face", 0x11: "drink query", 0x12: "message-remind query",
       0x13: "OTA (new)", 0x14: "sedentary query", 0x19: "device features", 0x1A: "functions", 0x1B: "assistant"}
KEYS = {
    0x02: {1: "time sync", 2: "alarms", 3: "step goal", 4: "profile", 5: "sedentary", 6: "wearing hand", 7: "notification switches",
           8: "power save", 9: "raise-to-wake", 10: "matching", 11: "find watch", 12: "camera mode", 13: "heart switch",
           17: "call state", 18: "message push", 26: "12/24 h", 36: "user name"},
    0x05: {1: "history request", 2: "steps per hour", 4: "heart rate", 5: "blood pressure", 6: "real-time steps", 7: "history start",
           8: "history end", 9: "sleep", 10: "today", 12: "total steps", 13: "temperature", 14: "SpO2", 15: "sport sessions"},
    0x0C: {1: "find phone start", 2: "camera shutter", 3: "camera open", 4: "camera close", 5: "heart test stopped",
           6: "BP test stopped", 8: "bind accepted", 9: "bind refused", 14: "temperature test stopped", 15: "find phone stop",
           16: "SpO2 test stopped", 19: "bond request (createBond trigger)"},
    0x0E: {1: "classic BT MAC (createBond trigger)", 3: "BT 3.0 info request", 4: "contact MD5"},
    0x0F: {1: "query", 2: "face list", 3: "select face", 4: "after sync", 5: "custom face layout", 6: "updated", 8: "updated",
           9: "face list", 10: "set code to update"},
    0x1A: {3: "social support", 5: "payment support", 7: "power-save support", 9: "power save set", 21: "exit find-phone",
           23: "altitude", 24: "location"},
}
# Payloads that carry personal data (C900-Q04/Q05): hidden unless --show-text.
PRIVATE = {(0x02, 18): "message text", (0x02, 17): "caller", (0x02, 36): "user name", (0x02, 4): "profile",
           (0x1A, 23): "altitude", (0x1A, 24): "location"}
FEATURE_BITS = [(1, 0x80, "isBLE3"), (15, 0x40, "isSupportPair (createBond after time ack)"),
                (18, 0x20, "binPreviewFlag (dial trim allowed)"), (25, 0x80, "hide HR auto test and DND")]


def checksum(frame):
    return (sum(frame) - frame[3]) & 0xFF


def label(cmd, key):
    return "%s / %s" % (CMD.get(cmd, "cmd 0x%02x ?" % cmd), KEYS.get(cmd, {}).get(key, "key %d" % key))


def short(u):
    return (u or "").lower()


def is_ota(u):
    u = short(u)
    return u in OTA_UUIDS or u.endswith("dcca9e") or (len(u) == 36 and u[4:8] in OTA_UUIDS and u.endswith("00805f9b34fb"))


def decode_frame(f, direction, show_text=False):
    d = {"dir": direction, "hex_len": len(f), "sum_ok": len(f) >= 4 and checksum(f) == f[3]}
    if f[0] == FD and len(f) >= 9:
        d.update(type="ack", cmd=f[4], key=f[5], x=(f[6] << 8) | f[7], status=f[8], label=label(f[4], f[5]))
        return d
    if len(f) < 9:
        d.update(type="short", raw=f.hex())
        return d
    plen = (f[7] << 8) | f[8]
    payload = f[9:9 + plen]
    d.update(type="cmd", cmd=f[4], ver=f[5], key=f[6], plen=plen, plen_ok=plen == len(f) - 9, label=label(f[4], f[6]))
    private = PRIVATE.get((f[4], f[6]))
    if private and not show_text:
        d["payload"] = "<%d bytes hidden (%s)>" % (len(payload), private)
    elif f[4] == 0x0E and f[6] == 1 and len(payload) >= 6:
        d["payload"] = "xx:xx:xx:xx:%02x:%02x (masked MAC)" % (payload[4], payload[5])
    else:
        d["payload"] = payload.hex()
    if f[4] in BLOCKED and direction == "tx":
        d["blocked"] = BLOCKED[f[4]]
    if f[4] == 0x19 and direction == "rx":
        d["features"] = features(payload)
    return d


def features(b):
    if not b:
        return {"marker_ok": False}
    out = {"marker_ok": b[0] == 0xAA, "len": len(b), "bits": {}}
    for idx, mask, name in FEATURE_BITS:
        out["bits"][name] = (bool(b[idx] & mask) if idx < len(b) else None)
    return out


class Reassembler:
    def __init__(self):
        self.buf, self.stray = bytearray(), 0

    def feed(self, chunk):
        if not self.buf and chunk and chunk[0] not in (DF, FD):
            self.stray += 1
            return []
        self.buf += chunk
        out = []
        while len(self.buf) >= 3:
            total = ((self.buf[1] << 8) | self.buf[2]) + 4
            if len(self.buf) < total:
                break
            out.append(bytes(self.buf[:total]))
            del self.buf[:total]
            if self.buf and self.buf[0] not in (DF, FD):
                self.stray += 1
                self.buf.clear()
        return out


def rows_from_capture(path):
    events = list(btcap.att_events(btcap.read_capture(path)))
    rows = [dict(r, value=bytes(r["value"])) for r in btcap.summarize(events)]
    hm, pend = btcap.handle_map(events), {}
    for ev in events:
        p, key = ev["pdu"], ev["conn"]
        if ev["opcode"] == 0x0A and len(p) >= 3:
            pend[key] = p[1] | (p[2] << 8)
        elif ev["opcode"] == 0x0B and key in pend:
            h = pend.pop(key)
            rows.append({"ts": ev["ts"], "kind": "R", "dir": ev["dir"], "handle": h, "uuid": hm.get(h), "value": p[1:]})
    rows.sort(key=lambda r: r["ts"])
    return rows


def rows_from_json(path):
    return [dict(r, value=bytes.fromhex(r["value"])) for r in json.load(open(path))]


def decode(rows, write=(WRITE_UUID, None), notify=(NOTIFY_UUID, None), show_text=False):
    def match(r, sel):
        u, h = sel
        return (h is not None and r["handle"] == h) or (h is None and short(r["uuid"]) == short(u))

    asm = {"tx": Reassembler(), "rx": Reassembler()}
    frames, reads = [], []
    s = {"frames_tx": 0, "frames_rx": 0, "bad_sum": 0, "versions_seen": set(), "features": None, "bond_triggers": [],
         "blocked_cmds": [], "ota_traffic": [], "battery": None, "hw_version": None, "fw_version": None}
    for r in rows:
        u, v = short(r["uuid"]), r["value"]
        if is_ota(u):
            s["ota_traffic"].append("%s %s %s" % (r["kind"], r["dir"], u))
            continue
        if r["kind"] == "R" or (r["kind"] == "N" and u == "2a19"):
            item = {"ts": r["ts"], "uuid": u, "hex": v.hex()}
            if u == "2a19" and v:
                s["battery"] = item["percent"] = v[0]
            elif u in ("2a26", "2a27"):
                item["text"] = v.decode("ascii", "replace")
                s["fw_version" if u == "2a26" else "hw_version"] = item["text"]
            elif u == "2a28":
                s["features"] = item["features"] = features(v)
            reads.append(item)
            continue
        if r["kind"] == "W" and match(r, write):
            d = "tx"
        elif r["kind"] == "N" and match(r, notify):
            d = "rx"
        else:
            continue
        for f in asm[d].feed(v):
            fr = decode_frame(f, d, show_text)
            fr["ts"] = r["ts"]
            frames.append(fr)
            s["frames_" + d] += 1
            if not fr["sum_ok"]:
                s["bad_sum"] += 1
            if fr["type"] == "cmd":
                if d == "tx":
                    s["versions_seen"].add(fr["ver"])
                if d == "rx" and (fr["cmd"], fr["key"]) in ((0x0C, 19), (0x0E, 1)):
                    s["bond_triggers"].append(fr["label"])
                if "blocked" in fr:
                    s["blocked_cmds"].append("0x%02x %s" % (fr["cmd"], fr["blocked"]))
                if "features" in fr and s["features"] is None:
                    s["features"] = fr["features"]
    feat = s["features"] or {}
    if (feat.get("bits") or {}).get("isSupportPair (createBond after time ack)"):
        s["bond_triggers"].append("feature b15 0x40 set")
    s["stray_chunks"] = asm["tx"].stray + asm["rx"].stray
    s["incomplete_bytes"] = len(asm["tx"].buf) + len(asm["rx"].buf)
    s["versions_seen"] = sorted(s["versions_seen"])
    return frames, reads, s


def render(frames, reads, s, t0=None):
    lines = []
    t0 = t0 if t0 is not None else min([f["ts"] for f in frames] + [r["ts"] for r in reads] or [0])
    for r in reads:
        extra = r.get("text") or ("%d %%" % r["percent"] if "percent" in r else "") or json.dumps(r.get("features", {}))
        lines.append("%8.3f READ %s %s %s" % (r["ts"] - t0, r["uuid"], r["hex"], extra))
    for f in frames:
        flag = "" if f["sum_ok"] else "  BAD-SUM"
        if f["type"] == "ack":
            lines.append("%8.3f %s ACK  cmd 0x%02x key %d x=%d status=%d  [%s]%s" % (f["ts"] - t0, f["dir"], f["cmd"], f["key"], f["x"], f["status"], f["label"], flag))
        elif f["type"] == "cmd":
            b = ("  BLOCKED-CMD %s" % f["blocked"]) if "blocked" in f else ""
            lines.append("%8.3f %s DF   cmd 0x%02x key %d ver %d plen %d  [%s]  %s%s%s" % (f["ts"] - t0, f["dir"], f["cmd"], f["key"], f["ver"], f["plen"], f["label"], f["payload"], flag, b))
        else:
            lines.append("%8.3f %s short frame %s%s" % (f["ts"] - t0, f["dir"], f.get("raw", ""), flag))
    lines += ["", "SUMMARY",
              "frames tx/rx: %d/%d, bad sums: %d, stray chunks: %d, incomplete bytes: %d" % (s["frames_tx"], s["frames_rx"], s["bad_sum"], s["stray_chunks"], s["incomplete_bytes"]),
              "version byte(s) seen in app frames: %s; 0x2A27: %s; 0x2A26: %s" % (s["versions_seen"] or "none", s["hw_version"], s["fw_version"]),
              "features: %s" % (json.dumps(s["features"]) if s["features"] else "not seen"),
              "battery: %s" % (("%d %%" % s["battery"]) if s["battery"] is not None else "not seen"),
              "bond triggers seen: %s" % (("yes: " + "; ".join(s["bond_triggers"])) if s["bond_triggers"] else "no"),
              "blocked cmds seen: %s" % (("YES: " + ", ".join(s["blocked_cmds"])) if s["blocked_cmds"] else "no"),
              "OTA/DFU traffic seen: %s" % (("YES (not decoded): %d PDU(s)" % len(s["ota_traffic"])) if s["ota_traffic"] else "no")]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--write-uuid", default=WRITE_UUID)
    ap.add_argument("--notify-uuid", default=NOTIFY_UUID)
    ap.add_argument("--write-handle", type=lambda x: int(x, 0))
    ap.add_argument("--notify-handle", type=lambda x: int(x, 0))
    ap.add_argument("--show-text", action="store_true", help="show message-push text (private; never paste into the repo)")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    try:
        rows = rows_from_json(a.input) if a.input.endswith(".json") else rows_from_capture(a.input)
    except (ValueError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    frames, reads, s = decode(rows, (a.write_uuid, a.write_handle), (a.notify_uuid, a.notify_handle), a.show_text)
    print(render(frames, reads, s))
    if a.json:
        json.dump({"frames": frames, "reads": reads, "summary": s}, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
