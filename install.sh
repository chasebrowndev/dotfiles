#!/usr/bin/env bash
# install.sh — deploy dotfiles to ~/.config
# Usage: ./install.sh [--waybar-theme THEME] [--hypr-theme THEME]
#   WAYBAR_THEME  waybar color theme (default: berserk)
#   HYPR_THEME    hyprland theme with keybinds (default: cyberpunk)
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HOME/.config"
WAYBAR_THEME="${WAYBAR_THEME:-berserk}"
HYPR_THEME="${HYPR_THEME:-cyberpunk}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --waybar-theme) WAYBAR_THEME="$2"; shift 2 ;;
        --hypr-theme)   HYPR_THEME="$2";   shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "dotfiles: $DOTFILES"
echo "waybar theme: $WAYBAR_THEME  |  hypr theme: $HYPR_THEME"

# ── helpers ────────────────────────────────────────────────────────────────────

die() { echo "error: $*" >&2; exit 1; }

safe_copy() {
    local src="$1" dst="$2"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
}

# Backs up real files; replaces existing symlinks in-place
safe_link() {
    local src="$1" dst="$2"
    mkdir -p "$(dirname "$dst")"
    if [[ -e "$dst" && ! -L "$dst" ]]; then
        local bak="${dst}.bak.$(date +%s)"
        echo "  backing up $dst → $bak"
        mv "$dst" "$bak"
    fi
    ln -sf "$src" "$dst"
}

# ── validate themes ────────────────────────────────────────────────────────────

[[ -d "$CONFIG/themes/$WAYBAR_THEME" ]] || \
    die "waybar theme '$WAYBAR_THEME' not found in $CONFIG/themes/"
[[ -f "$CONFIG/themes/$WAYBAR_THEME/waybar.jsonc" ]] || \
    die "missing $CONFIG/themes/$WAYBAR_THEME/waybar.jsonc"
[[ -d "$CONFIG/themes/$HYPR_THEME" ]] || \
    die "hypr theme '$HYPR_THEME' not found in $CONFIG/themes/"
[[ -f "$CONFIG/themes/$HYPR_THEME/hypr.conf" ]] || \
    die "missing $CONFIG/themes/$HYPR_THEME/hypr.conf"

# ── hyprland ───────────────────────────────────────────────────────────────────

echo "→ hyprland"
safe_copy "$DOTFILES/.config/hypr/hyprland.conf" "$CONFIG/hypr/hyprland.conf"
safe_copy "$DOTFILES/.config/hypr/theme.conf"    "$CONFIG/hypr/theme.conf"
safe_link "$CONFIG/themes/$HYPR_THEME/hypr.conf" "$CONFIG/hypr/hypr.conf"

# ── kitty ──────────────────────────────────────────────────────────────────────

echo "→ kitty"
safe_copy "$DOTFILES/.config/kitty/kitty.conf" "$CONFIG/kitty/kitty.conf"

# ── themes ─────────────────────────────────────────────────────────────────────

echo "→ themes"
for theme_dir in "$DOTFILES/.config/themes"/*/; do
    theme="$(basename "$theme_dir")"
    mkdir -p "$CONFIG/themes/$theme"
    for f in "$theme_dir"*.conf "$theme_dir"*.css "$theme_dir"*.jsonc; do
        [[ -f "$f" ]] && cp "$f" "$CONFIG/themes/$theme/"
    done
done

# ── waybar scripts ─────────────────────────────────────────────────────────────

echo "→ waybar scripts"
mkdir -p "$CONFIG/waybar/scripts"
cp "$DOTFILES/.config/waybar/scripts/"*.py "$CONFIG/waybar/scripts/"
chmod +x "$CONFIG/waybar/scripts/"*.py

# ── waybar theme symlinks ──────────────────────────────────────────────────────

echo "→ waybar symlinks → $WAYBAR_THEME"
safe_link "$CONFIG/themes/$WAYBAR_THEME/waybar.jsonc" "$CONFIG/waybar/config.jsonc"
safe_link "$CONFIG/themes/$WAYBAR_THEME/waybar.css"   "$CONFIG/waybar/style.css"

# ── reload ─────────────────────────────────────────────────────────────────────

echo ""
echo "Done. Reload:"
echo "  hyprctl reload          — apply hyprland config"
echo "  killall waybar; waybar & — restart waybar"
