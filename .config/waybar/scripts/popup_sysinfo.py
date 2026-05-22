#!/usr/bin/env python3
import os
import sys
import signal
import json
import time
import subprocess

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell, Gdk, GLib

PID_FILE = '/tmp/waybar-popup-sysinfo.pid'
WIDTH = 320
TOP = 46

CSS = b"""
* { font-family: monospace; font-size: 12px; }
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
.section {
    color: #882200;
    font-size: 10px;
    padding: 5px 12px 1px;
    letter-spacing: 1px;
}
.row {
    padding: 1px 14px 1px;
    color: #999;
}
separator {
    background: rgba(255,0,0,0.07);
    min-height: 1px;
    margin: 2px 0;
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


def read_cpu_stats():
    lines = open('/proc/stat').readlines()
    stats = {}
    for line in lines:
        parts = line.split()
        if parts[0].startswith('cpu'):
            nums = [int(x) for x in parts[1:8]]
            stats[parts[0]] = (nums[3], sum(nums))  # (idle, total)
    return stats



def mem_info():
    data = {}
    for line in open('/proc/meminfo'):
        k, v = line.split(':')
        data[k.strip()] = int(v.split()[0])
    total = data['MemTotal']
    used = total - data['MemAvailable']
    st = data.get('SwapTotal', 0)
    sf = data.get('SwapFree', 0)
    return {
        'total': total / 1048576,
        'used': used / 1048576,
        'pct': round(100 * used / total) if total else 0,
        'swap_total': st / 1048576,
        'swap_used': (st - sf) / 1048576,
        'swap_pct': round(100 * (st - sf) / st) if st else 0,
    }


def disk_info(path):
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize / 1073741824
        free = st.f_bfree * st.f_frsize / 1073741824
        used = total - free
        return {'total': total, 'used': used, 'pct': round(100 * used / total) if total else 0}
    except Exception:
        return None


def uptime_str():
    secs = float(open('/proc/uptime').read().split()[0])
    d, rem = divmod(int(secs), 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    parts = []
    if d:
        parts.append(f'{d}d')
    if h:
        parts.append(f'{h}h')
    parts.append(f'{m}m')
    return ' '.join(parts)


def bbar(pct, length=8):
    filled = int(length * pct / 100)
    return '█' * filled + '░' * (length - filled)


# first CPU snapshot — no sleep; second snapshot happens after show_all
s1 = read_cpu_stats()
mem = mem_info()
disk_root = disk_info('/')
disk_home = disk_info('/home') if os.path.ismount('/home') else None
la = open('/proc/loadavg').read().split()[:3]
up = uptime_str()

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


def add_title(text):
    l = Gtk.Label(label=text)
    l.get_style_context().add_class('title')
    l.set_halign(Gtk.Align.START)
    box.pack_start(l, False, False, 0)


def add_section(text):
    l = Gtk.Label(label=text.upper())
    l.get_style_context().add_class('section')
    l.set_halign(Gtk.Align.START)
    box.pack_start(l, False, False, 0)


def add_row(markup):
    l = Gtk.Label()
    l.set_markup(markup)
    l.get_style_context().add_class('row')
    l.set_halign(Gtk.Align.START)
    box.pack_start(l, False, False, 0)


def add_sep():
    box.pack_start(Gtk.Separator(), False, False, 0)


add_title('sysinfo')

# CPU — placeholder labels, filled in after 350ms sample
add_section('cpu')
_cpu_lbls = {}
_cores = sorted([k for k in s1 if k != 'cpu'], key=lambda x: int(x[3:]))

def _cpu_lbl(markup, key):
    l = Gtk.Label()
    l.set_markup(markup)
    l.get_style_context().add_class('row')
    l.set_halign(Gtk.Align.START)
    box.pack_start(l, False, False, 0)
    _cpu_lbls[key] = l

_cpu_lbl(
    f"<span color='#cc4400'>{'░' * 8}</span>"
    f"  <span color='#887766'>  ?%  overall</span>",
    'cpu'
)
for _c in _cores:
    _cpu_lbl(
        f"<span color='#444'>{'░' * 8}</span>"
        f"  <span color='#554433'>  ?%  {_c}</span>",
        _c
    )

add_sep()

# Memory
add_section('memory')
add_row(
    f"<span color='#cc4400'>{bbar(mem['pct'])}</span>"
    f"  <span color='#ee5500'>{mem['used']:.1f}G</span>"
    f"<span color='#555'>/{mem['total']:.1f}G</span>"
    f"  <span color='#885533'>({mem['pct']}%)</span>"
)
if mem['swap_total'] > 0:
    add_row(
        f"<span color='#777'>swap</span>"
        f"  <span color='#aa3300'>{mem['swap_used']:.1f}G</span>"
        f"<span color='#555'>/{mem['swap_total']:.1f}G</span>"
        f"  <span color='#775533'>({mem['swap_pct']}%)</span>"
    )

add_sep()

# Disk
add_section('disk')
if disk_root:
    add_row(
        f"<span color='#777'>/      </span>"
        f"<span color='#cc4400'>{bbar(disk_root['pct'])}</span>"
        f"  <span color='#ee5500'>{disk_root['used']:.0f}G</span>"
        f"<span color='#555'>/{disk_root['total']:.0f}G</span>"
    )
if disk_home:
    add_row(
        f"<span color='#777'>/home  </span>"
        f"<span color='#cc4400'>{bbar(disk_home['pct'])}</span>"
        f"  <span color='#ee5500'>{disk_home['used']:.0f}G</span>"
        f"<span color='#555'>/{disk_home['total']:.0f}G</span>"
    )

add_sep()

# System
add_section('system')
add_row(f"<span color='#777'>load  </span><span color='#cc4400'>{la[0]}  {la[1]}  {la[2]}</span>")
add_row(f"<span color='#777'>up    </span><span color='#cc4400'>{up}</span>")

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


def _update_cpu():
    s2 = read_cpu_stats()
    cpus = {}
    for k in s1:
        if k not in s2:
            continue
        i1, t1 = s1[k]
        i2, t2 = s2[k]
        dt = t2 - t1
        cpus[k] = round(100 * (1 - (i2 - i1) / dt)) if dt else 0
    overall = cpus.get('cpu', 0)
    if 'cpu' in _cpu_lbls:
        _cpu_lbls['cpu'].set_markup(
            f"<span color='#cc4400'>{bbar(overall)}</span>"
            f"  <span color='#ee5500'>{overall:>3}%</span>"
            f"  <span color='#887766'>overall</span>"
        )
    for c in _cores:
        if c in _cpu_lbls and c in cpus:
            pct = cpus[c]
            _cpu_lbls[c].set_markup(
                f"<span color='#aa3300'>{bbar(pct)}</span>"
                f"  <span color='#cc4400'>{pct:>3}%</span>"
                f"  <span color='#665544'>{c}</span>"
            )
    return False

GLib.timeout_add(350, _update_cpu)

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
