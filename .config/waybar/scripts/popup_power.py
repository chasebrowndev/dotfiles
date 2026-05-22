#!/usr/bin/env python3
import os
import sys
import signal
import json
import subprocess

import time
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell, Gdk, GLib

PID_FILE = '/tmp/waybar-popup-power.pid'
WIDTH = 200
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
button {
    background: transparent;
    border: none;
    border-top: 1px solid rgba(255,0,0,0.1);
    color: #bbb;
    padding: 9px 14px;
    font-family: monospace;
    font-size: 13px;
}
button:first-child { border-top: none; }
button:hover {
    background: rgba(255,0,0,0.1);
    color: #ff3300;
}
"""

# toggle: if already open, kill and exit
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

# position popup centered on cursor
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

title = Gtk.Label(label='power')
title.get_style_context().add_class('title')
title.set_halign(Gtk.Align.START)
box.pack_start(title, False, False, 0)

def _exec(cmd):
    subprocess.Popen(cmd, shell=True)
    _close()

for lbl, cmd in [
    ('  lock',     'loginctl lock-session'),
    ('  suspend',  'systemctl suspend'),
    ('↺  reboot',  'systemctl reboot'),
    ('⏻  shutdown', 'systemctl poweroff'),
]:
    b = Gtk.Button(label=lbl)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.connect('clicked', lambda _, c=cmd: _exec(c))
    box.pack_start(b, False, False, 0)

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
