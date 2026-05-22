#!/usr/bin/env bash
# switch-theme.sh <theme> — switch active waybar + hypr theme
# If the theme has a waybar config, it becomes the active bar theme.
# If it has a hypr.conf, it becomes the active hyprland theme.
# Both can differ: e.g., berserk bar + cyberpunk hypr.
set -euo pipefail

CONFIG="$HOME/.config"
THEME="${1:-}"

if [[ -z "$THEME" ]]; then
    echo "Usage: ./switch-theme.sh <theme>"
    echo ""
    echo "Available themes:"
    ls "$CONFIG/themes/"
    exit 1
fi

[[ -d "$CONFIG/themes/$THEME" ]] || {
    echo "Theme '$THEME' not found. Available:"
    ls "$CONFIG/themes/"
    exit 1
}

changed=0

# ── waybar ─────────────────────────────────────────────────────────────────────

if [[ -f "$CONFIG/themes/$THEME/waybar.jsonc" ]]; then
    ln -sf "$CONFIG/themes/$THEME/waybar.jsonc" "$CONFIG/waybar/config.jsonc"
    ln -sf "$CONFIG/themes/$THEME/waybar.css"   "$CONFIG/waybar/style.css"
    echo "waybar → $THEME"
    changed=1
fi

# ── hyprland ───────────────────────────────────────────────────────────────────

if [[ -f "$CONFIG/themes/$THEME/hypr.conf" ]]; then
    ln -sf "$CONFIG/themes/$THEME/hypr.conf" "$CONFIG/hypr/hypr.conf"
    echo "hypr → $THEME"
    hyprctl reload 2>/dev/null && echo "hyprland reloaded" || true
    changed=1
fi

[[ $changed -eq 0 ]] && echo "No config files found for theme '$THEME'"

# ── restart waybar ─────────────────────────────────────────────────────────────

if [[ $changed -eq 1 ]]; then
    killall waybar 2>/dev/null || true
    waybar &
    disown
    echo "waybar restarted"
fi
