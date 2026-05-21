#!/usr/bin/env python3
import json
import time


def bar(pct, length=5):
    filled = int(length * pct / 100)
    return "█" * filled + "░" * (length - filled)


def color(pct):
    t = max(0.0, min(1.0, pct / 100))
    r = int(0x66 + (0xff - 0x66) * t)
    return f"#{r:02x}0000"


def cpu_pct():
    def read():
        with open("/proc/stat") as f:
            parts = f.readline().split()
        idle = int(parts[4])
        total = sum(int(x) for x in parts[1:])
        return idle, total

    i1, t1 = read()
    time.sleep(0.25)
    i2, t2 = read()
    if t2 == t1:
        return 0
    return round(100 * (1 - (i2 - i1) / (t2 - t1)))


def mem_info():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v = line.split(":")
            info[k.strip()] = int(v.split()[0])
    total = info["MemTotal"]
    used = total - info["MemAvailable"]
    return round(100 * used / total), used / 1048576


sep = "<span color='#333'>  |  </span>"

cpu = cpu_pct()
mem_pct, mem_used = mem_info()
cc, mc = color(cpu), color(mem_pct)

text = (
    f"<span color='#888'>CPU</span> "
    f"<span color='#444'>[</span><span color='{cc}'>{bar(cpu)}</span><span color='#444'>]</span> "
    f"<span color='{cc}'>{cpu}%</span>"
    f"{sep}"
    f"<span color='#888'>MEM</span> "
    f"<span color='#444'>[</span><span color='{mc}'>{bar(mem_pct)}</span><span color='#444'>]</span> "
    f"<span color='{mc}'>{mem_used:.1f}G</span>"
)

print(json.dumps({"text": text}))
