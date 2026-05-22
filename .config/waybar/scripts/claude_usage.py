#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
import json
import os
import sys
import requests
from datetime import datetime, timezone

CREDENTIALS_FILE = os.path.expanduser("~/.claude/.credentials.json")
CACHE_FILE = "/tmp/claude_usage_cache.json"
CACHE_TTL = 300  # 5 minutes


def get_token():
    try:
        with open(CREDENTIALS_FILE) as f:
            data = json.load(f)
        oauth = data["claudeAiOauth"]
        expires_at = oauth.get("expiresAt", 0)
        if expires_at > 1e12:
            expires_at /= 1000
        if datetime.now(timezone.utc).timestamp() > expires_at:
            return None, "Token expired — reopen Claude Code"
        return oauth["accessToken"], None
    except FileNotFoundError:
        return None, f"Credentials not found: {CREDENTIALS_FILE}"
    except Exception as e:
        return None, str(e)


def get_cached():
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        if datetime.now(timezone.utc).timestamp() - cache["timestamp"] < CACHE_TTL:
            return cache["data"]
    except Exception:
        pass
    return None


def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"timestamp": datetime.now(timezone.utc).timestamp(), "data": data}, f)
    except Exception:
        pass


def fetch_usage(token):
    cached = get_cached()
    if cached:
        return cached, None
    try:
        resp = requests.get(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
                "User-Agent": "claude-code/2.0.32",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return None, str(data["error"])
        save_cache(data)
        return data, None
    except Exception as e:
        return None, str(e)


def format_reset(resets_at_str):
    if not resets_at_str:
        return "no active session"
    try:
        reset_dt = datetime.fromisoformat(resets_at_str.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return "?"
    diff = reset_dt - datetime.now(timezone.utc)
    total = int(diff.total_seconds())
    if total <= 0:
        return "now"
    h, rem = divmod(total, 3600)
    m = rem // 60
    return f"{h}h {m}m" if h > 0 else f"{m}m"


def bar(pct, length=8):
    filled = int(length * pct / 100)
    return "█" * filled + "░" * (length - filled)


def color(pct):
    # Anthropic orange (#d97757) → red (#ff003c)
    t = max(0.0, min(1.0, pct / 100))
    r = int(0xd9 + (0xff - 0xd9) * t)
    g = int(0x77 + (0x00 - 0x77) * t)
    b = int(0x57 + (0x3c - 0x57) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def main():
    token, err = get_token()
    if not token:
        print(json.dumps({"text": f"<span color='#ff003c'> AUTH ERROR: {err}</span>"}))
        return

    data, err = fetch_usage(token)
    if not data:
        print(json.dumps({"text": f"<span color='#ff003c'> FETCH ERROR: {err}</span>"}))
        return

    five = data.get("five_hour", {})
    seven = data.get("seven_day", {})

    five_pct = round(float(five.get("utilization") or 0))
    seven_pct = round(float(seven.get("utilization") or 0))
    five_reset = format_reset(five.get("resets_at"))
    seven_reset = format_reset(seven.get("resets_at"))

    five_c = color(five_pct)
    seven_c = color(seven_pct)

    five_label = f"{five_pct}%" if five.get("resets_at") else "--"
    seven_label = f"{seven_pct}%" if seven.get("resets_at") else "--"

    sep = "<span color='#555'>  |  </span>"

    text = (
        f"<span color='#888'> CLAUDE</span>{sep}"
        f"<span color='#aaa'>SESSION</span>  "
        f"<span color='#666'>[</span><span color='{five_c}'>{bar(five_pct)}</span><span color='#666'>]</span>  "
        f"<span color='{five_c}'>{five_label}</span>  "
        f"<span color='#888'>RESETS</span> <span color='#aaa'>{five_reset}</span>"
        f"{sep}"
        f"<span color='#aaa'>WEEKLY</span>  "
        f"<span color='#666'>[</span><span color='{seven_c}'>{bar(seven_pct)}</span><span color='#666'>]</span>  "
        f"<span color='{seven_c}'>{seven_label}</span>  "
        f"<span color='#888'>RESETS</span> <span color='#aaa'>{seven_reset}</span>"
    )

    extra = data.get("extra_usage", {})
    if extra.get("is_enabled"):
        extra_pct = round(float(extra.get("utilization") or 0))
        used = extra.get("used_credits", 0) / 100
        limit = extra.get("monthly_limit", 0) / 100
        extra_c = color(extra_pct)
        text += (
            f"{sep}"
            f"<span color='#aaa'>EXTRA</span>  "
            f"<span color='#666'>[</span><span color='{extra_c}'>{bar(extra_pct)}</span><span color='#666'>]</span>  "
            f"<span color='{extra_c}'>{extra_pct}%</span>  "
            f"<span color='#888'>${used:.2f}</span><span color='#555'>/</span><span color='#888'>${limit:.2f}</span>"
        )

    print(json.dumps({"text": text}))


if __name__ == "__main__":
    main()
