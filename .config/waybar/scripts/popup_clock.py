#!/usr/bin/env python3
import os
import sys
import signal
import json
import subprocess
from datetime import datetime, timezone

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
import time
from gi.repository import Gtk, GtkLayerShell, Gdk, GLib

PID_FILE = '/tmp/waybar-popup-clock.pid'
WIDTH = 260
TOP = 46

CSS = b"""
* { font-family: monospace; font-size: 13px; }
window {
    background: rgba(26,26,26,0.92);
    border: 1px solid rgba(255,0,0,0.5);
}
.title {
    color: #aa3300;
    font-size: 10px;
    padding: 5px 12px 4px;
    border-bottom: 1px solid rgba(255,0,0,0.15);
}
.big-time {
    color: #ee5500;
    font-size: 28px;
    padding: 8px 14px 2px;
    letter-spacing: 2px;
}
.big-date {
    color: #cc4400;
    font-size: 15px;
    padding: 0 14px 6px;
}
.row {
    color: #777;
    font-size: 12px;
    padding: 2px 14px;
}
.row-val { color: #cc4400; }
separator {
    background: rgba(255,0,0,0.08);
    min-height: 1px;
    margin: 3px 0;
}
"""

# toggle
if os.path.exists(PID_FILE):
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, ValueError, OSError):
        pass
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass
    sys.exit(0)

now = datetime.now()
utc_now = datetime.now(timezone.utc)

day_of_year = now.strftime('%j').lstrip('0') or '0'
week_num    = now.strftime('%V').lstrip('0') or '0'
unix_ts     = str(int(now.timestamp()))
tz_name     = now.astimezone().tzname()
utc_offset  = now.astimezone().strftime('%z')
utc_str     = f"UTC{utc_offset[:3]}:{utc_offset[3:]}" if len(utc_offset) == 5 else utc_offset

# position
try:
    import concurrent.futures as _cf
    with _cf.ThreadPoolExecutor(max_workers=2) as _ex:
        _fc = _ex.submit(lambda: json.loads(subprocess.check_output(['hyprctl', 'cursorpos', '-j']))['x'])
        _fm = _ex.submit(lambda: json.loads(subprocess.check_output(['hyprctl', 'monitors', '-j']))[0]['width'])
        cx, sw = _fc.result(), _fm.result()
    left = max(10, min(cx - WIDTH // 2, sw - WIDTH - 10))
except Exception:
    left = 200

win = Gtk.Window()
win.set_size_request(WIDTH, -1)

GtkLayerShell.init_for_window(win)
GtkLayerShell.set_layer(win, GtkLayerShell.Layer.TOP)
GtkLayerShell.set_namespace(win, 'waybar-popup')
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.LEFT, True)
GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 6)
GtkLayerShell.set_margin(win, GtkLayerShell.Edge.LEFT, left)
GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)

css_prov = Gtk.CssProvider()
css_prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), css_prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
win.add(box)

title = Gtk.Label(label='date & time')
title.get_style_context().add_class('title')
title.set_halign(Gtk.Align.START)
box.pack_start(title, False, False, 0)

time_lbl = Gtk.Label(label=now.strftime('%H:%M:%S'))
time_lbl.get_style_context().add_class('big-time')
time_lbl.set_halign(Gtk.Align.START)
box.pack_start(time_lbl, False, False, 0)

date_lbl = Gtk.Label(label=now.strftime('%A,  %d %B %Y'))
date_lbl.get_style_context().add_class('big-date')
date_lbl.set_halign(Gtk.Align.START)
box.pack_start(date_lbl, False, False, 0)

box.pack_start(Gtk.Separator(), False, False, 0)


def add_row(key, val):
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    row.get_style_context().add_class('row')
    k = Gtk.Label(label=f'{key}:')
    k.set_halign(Gtk.Align.START)
    v = Gtk.Label(label=val)
    v.get_style_context().add_class('row-val')
    v.set_halign(Gtk.Align.START)
    row.pack_start(k, False, False, 0)
    row.pack_start(v, False, False, 0)
    box.pack_start(row, False, False, 0)


add_row('day',      f"day {day_of_year} of {now.strftime('%Y')} ({now.strftime('%A')[:3]})")
add_row('week',     f"week {week_num}")
add_row('timezone', f"{tz_name}  ({utc_str})")
add_row('unix',     unix_ts)

win.connect('destroy', Gtk.main_quit)
win.connect('key-press-event', lambda w, e: _close() if e.keyval == Gdk.KEY_Escape else None)

with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))

win.show_all()
_t0 = [None]

def _drop():
    if _t0[0] is None:
        _t0[0] = time.monotonic()
    p = min(1.0, (time.monotonic() - _t0[0]) * 1000 / 220)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, int(6 + (TOP - 6) * (1 - (1 - p) ** 3)))
    return p < 1.0

GLib.timeout_add(14, _drop)

_closing = [False]

def _close():
    if _closing[0]:
        return
    _closing[0] = True
    _c0 = [None]
    def _rise():
        if _c0[0] is None:
            _c0[0] = time.monotonic()
        p = min(1.0, (time.monotonic() - _c0[0]) * 1000 / 160)
        ep = p * p
        GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, int(TOP - (TOP + 400) * ep))
        win.set_opacity(max(0.0, 1.0 - ep))
        if p >= 1.0:
            win.destroy()
            return False
        return True
    GLib.timeout_add(14, _rise)
signal.signal(signal.SIGTERM, lambda *_: GLib.idle_add(_close))
Gtk.main()

try:
    os.remove(PID_FILE)
except FileNotFoundError:
    pass
