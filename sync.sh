#!/usr/bin/env bash
# sync.sh — copy live ~/.config changes back into the dotfiles repo
# Run this before committing when you've tweaked configs directly.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HOME/.config"

echo "syncing $CONFIG → $DOTFILES"

# ── hyprland ───────────────────────────────────────────────────────────────────

cp "$CONFIG/hypr/hyprland.conf" "$DOTFILES/.config/hypr/"
cp "$CONFIG/hypr/theme.conf"    "$DOTFILES/.config/hypr/"

# ── kitty ──────────────────────────────────────────────────────────────────────

cp "$CONFIG/kitty/kitty.conf" "$DOTFILES/.config/kitty/"

# ── themes ─────────────────────────────────────────────────────────────────────

for theme in berserk cyberpunk eldensote kaneki; do
    src="$CONFIG/themes/$theme"
    dst="$DOTFILES/.config/themes/$theme"
    [[ -d "$src" ]] || continue
    mkdir -p "$dst"
    for ext in conf css jsonc; do
        for f in "$src"/*."$ext"; do
            [[ -f "$f" ]] && cp "$f" "$dst/"
        done
    done
done

# ── waybar scripts ─────────────────────────────────────────────────────────────

cp "$CONFIG/waybar/scripts/"*.py "$DOTFILES/.config/waybar/scripts/"

echo ""
echo "Synced. Review changes:"
echo "  git -C $DOTFILES diff --stat"
echo "  git -C $DOTFILES diff"
