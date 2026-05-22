#!/usr/bin/env python3
import json
import subprocess


def bar(pct, length=5):
    filled = int(length * pct / 100)
    return '█' * filled + '░' * (length - filled)


def color(pct):
    t = min(1.0, pct / 100)
    r = int(0x88 + (0xff - 0x88) * t)
    return f'#{r:02x}0000'


try:
    out = subprocess.check_output(
        ['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'],
        stderr=subprocess.DEVNULL
    ).decode().strip()
    parts = out.split()
    vol = round(float(parts[1]) * 100)
    muted = '[MUTED]' in out

    if muted:
        text = (
            f"<span color='#aaa'>VOL</span> "
            f"<span color='#666'>[</span><span color='#555'>{bar(0)}</span><span color='#666'>]</span> "
            f"<span color='#660000'>{vol}% [M]</span>"
        )
    else:
        c = color(vol)
        text = (
            f"<span color='#aaa'>VOL</span> "
            f"<span color='#666'>[</span><span color='{c}'>{bar(vol)}</span><span color='#666'>]</span> "
            f"<span color='{c}'>{vol}%</span>"
        )
except Exception:
    text = "<span color='#555'>VOL</span> <span color='#550000'>err</span>"

print(json.dumps({'text': text}))
