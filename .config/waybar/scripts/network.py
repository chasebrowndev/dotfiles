#!/usr/bin/env python3
import json
import re
import subprocess


def bar(pct, length=5):
    filled = int(length * pct / 100)
    return '█' * filled + '░' * (length - filled)


def color(pct):
    t = min(1.0, pct / 100)
    r = int(0x88 + (0xff - 0x88) * t)
    return f'#{r:02x}0000'


def rssi_to_pct(rssi_dbm):
    return max(0, min(100, 2 * (rssi_dbm + 100)))


def parse_iwctl(iface='wlan0'):
    out = subprocess.check_output(
        ['iwctl', 'station', iface, 'show'], stderr=subprocess.DEVNULL
    ).decode()
    out = re.sub(r'\x1b\[[0-9;]*m', '', out)  # strip ANSI
    fields = {}
    for line in out.splitlines():
        line = line.rstrip()
        m = re.match(r'\s+(?:Settable\s+)?(\S[\w ]+\S)\s{2,}(.+)', line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


try:
    fields = parse_iwctl()
    state = fields.get('State', '')
    ssid = fields.get('Connected network')
    rssi_str = fields.get('RSSI', '')

    if state == 'connected' and ssid:
        m = re.search(r'(-\d+)', rssi_str)
        rssi = int(m.group(1)) if m else -80
        pct = rssi_to_pct(rssi)
        c = color(pct)
        label = ssid[:10] + '…' if len(ssid) > 11 else ssid
        text = (
            f"<span color='#aaa'>NET</span> "
            f"<span color='#666'>[</span><span color='{c}'>{bar(pct)}</span><span color='#666'>]</span> "
            f"<span color='#888'>{label}</span>"
        )
    else:
        text = "<span color='#555'>NET</span> <span color='#550000'>offline</span>"
except Exception:
    text = "<span color='#555'>NET</span> <span color='#550000'>err</span>"

print(json.dumps({'text': text}))
