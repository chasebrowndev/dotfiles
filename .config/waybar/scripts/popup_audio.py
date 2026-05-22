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

PID_FILE = '/tmp/waybar-popup-audio.pid'
WIDTH = 250
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
.vol-display {
    color: #cc4400;
    padding: 7px 14px 2px;
    font-size: 14px;
}
.sink-label {
    color: #775533;
    font-size: 11px;
    padding: 0 14px 5px;
}
separator {
    background: rgba(255,0,0,0.1);
    min-height: 1px;
}
button {
    background: transparent;
    border: none;
    border-top: 1px solid rgba(255,0,0,0.1);
    color: #bbb;
    padding: 8px 14px;
    font-family: monospace;
    font-size: 13px;
}
.btn-row button {
    border-top: none;
    border-right: 1px solid rgba(255,0,0,0.1);
    padding: 9px 0;
}
.btn-row button:last-child { border-right: none; }
button:hover {
    background: rgba(255,0,0,0.1);
    color: #ff3300;
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


def get_vol():
    out = subprocess.check_output(
        ['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], stderr=subprocess.DEVNULL
    ).decode().strip()
    parts = out.split()
    return round(float(parts[1]) * 100), '[MUTED]' in out


def get_sink():
    try:
        default = subprocess.check_output(
            ['pactl', 'get-default-sink'], stderr=subprocess.DEVNULL
        ).decode().strip()
        if 'analog' in default:
            return 'Analog Stereo'
        if 'hdmi' in default.lower():
            return 'HDMI'
        if 'bluetooth' in default.lower() or 'bluez' in default.lower():
            return 'Bluetooth'
        return default.split('.')[-1].replace('-', ' ').title()
    except Exception:
        return ''


def vbar(pct, length=10):
    filled = int(length * pct / 100)
    return '█' * filled + '░' * (length - filled)


vol, muted = get_vol()
sink = get_sink()

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

title = Gtk.Label(label='audio')
title.get_style_context().add_class('title')
title.set_halign(Gtk.Align.START)
box.pack_start(title, False, False, 0)

mute_str = '  [MUTED]' if muted else ''
vol_lbl = Gtk.Label(label=f'{vbar(0 if muted else vol)}  {vol}%{mute_str}')
vol_lbl.get_style_context().add_class('vol-display')
vol_lbl.set_halign(Gtk.Align.START)
box.pack_start(vol_lbl, False, False, 0)

if sink:
    sink_lbl = Gtk.Label(label=f'sink: {sink}')
    sink_lbl.get_style_context().add_class('sink-label')
    sink_lbl.set_halign(Gtk.Align.START)
    box.pack_start(sink_lbl, False, False, 0)

box.pack_start(Gtk.Separator(), False, False, 0)


def refresh_label():
    v, m = get_vol()
    ms = '  [MUTED]' if m else ''
    vol_lbl.set_text(f'{vbar(0 if m else v)}  {v}%{ms}')
    return False


def adj_vol(delta):
    if delta > 0:
        subprocess.Popen(f'wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ {abs(delta)}%+', shell=True)
    else:
        subprocess.Popen(f'wpctl set-volume @DEFAULT_AUDIO_SINK@ {abs(delta)}%-', shell=True)
    GLib.timeout_add(80, refresh_label)


def toggle_mute():
    subprocess.Popen('wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle', shell=True)
    GLib.timeout_add(80, refresh_label)


btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True)
btn_row.get_style_context().add_class('btn-row')
box.pack_start(btn_row, False, False, 0)

for lbl_txt, fn in [
    ('−10%', lambda _: adj_vol(-10)),
    ('−5%',  lambda _: adj_vol(-5)),
    ('mute', lambda _: toggle_mute()),
    ('+5%',  lambda _: adj_vol(5)),
    ('+10%', lambda _: adj_vol(10)),
]:
    b = Gtk.Button(label=lbl_txt)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.connect('clicked', fn)
    btn_row.pack_start(b, True, True, 0)

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
