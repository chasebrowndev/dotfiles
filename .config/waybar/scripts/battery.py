#!/usr/bin/env python3
import json
import os


def bar(pct, length=5):
    filled = int(length * pct / 100)
    return "█" * filled + "░" * (length - filled)


def color(pct):
    t = max(0.0, min(1.0, 1 - pct / 100))
    r = int(0x88 + (0xff - 0x88) * t)
    return f"#{r:02x}0000"


def find_battery():
    base = "/sys/class/power_supply"
    best, best_full = None, 0
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name)
        try:
            if open(os.path.join(p, "type")).read().strip() != "Battery":
                continue
            full = int(open(os.path.join(p, "energy_full")).read().strip())
            if full > best_full:
                best, best_full = p, full
        except OSError:
            pass
    return best


bat = find_battery()

if not bat:
    print(json.dumps({"text": "<span color='#666'>NO BAT</span>"}))
    exit()


def read(f):
    try:
        return open(os.path.join(bat, f)).read().strip()
    except OSError:
        return None


pct = int(read("capacity") or 0)
status = read("status") or "Unknown"
charging = status in ("Charging", "Full")
c = color(pct)

energy_now = int(read("energy_now") or 0)
energy_full = int(read("energy_full") or 0)
power = int(read("power_now") or 0)

if status == "Full":
    time_str = "full"
elif power > 0:
    remaining = (energy_full - energy_now) if charging else energy_now
    hours = remaining / power
    h, m = int(hours), int((hours % 1) * 60)
    time_str = f"{h}h{m:02d}m" if h > 0 else f"{m}m"
else:
    time_str = ""

indicator = " <span color='#aaa'>↑</span>" if charging else ""
time_part = f" <span color='#888'>{time_str}</span>" if time_str else ""

text = (
    f"<span color='#aaa'>BAT</span> "
    f"<span color='#666'>[</span><span color='{c}'>{bar(pct)}</span><span color='#666'>]</span> "
    f"<span color='{c}'>{pct}%</span>"
    f"{time_part}{indicator}"
)

print(json.dumps({"text": text}))
