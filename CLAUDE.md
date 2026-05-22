# Claude Code — Dotfiles

Personal Hyprland + Waybar + Kitty rice for Arch Linux.

## Repo layout

```
dotfiles/
├── .config/
│   ├── hypr/
│   │   ├── hyprland.conf     — machine-local: monitors, input devices
│   │   └── theme.conf        — base WM look (colors, animations, gaps)
│   ├── kitty/
│   │   └── kitty.conf        — terminal (dark red/black, JetBrainsMono NF)
│   ├── themes/               — each theme has hypr.conf + waybar.{jsonc,css}
│   │   ├── berserk/          — active waybar theme (dark red-on-black)
│   │   ├── cyberpunk/        — active hypr theme (keybinds, popups)
│   │   ├── eldensote/
│   │   └── kaneki/
│   └── waybar/
│       └── scripts/          — Python widgets + GTK3 popup dropdowns
├── install.sh                — deploy to ~/.config (idempotent)
├── sync.sh                   — pull live changes back into this repo
└── switch-theme.sh           — swap active theme and restart waybar
```

**Wallpapers are not tracked** — they're large binaries. Copy them manually to `~/.config/themes/<name>/wallpaper.jpg` and set via `swww img`.

## Quick start (fresh machine)

```bash
git clone git@github.com:chasebrowndev/dotfiles.git
cd dotfiles
chmod +x install.sh sync.sh switch-theme.sh

# Themes land in ~/.config/themes first (install.sh copies them)
# then the symlinks are created. Order matters.
./install.sh
```

Install with non-default themes:
```bash
WAYBAR_THEME=berserk HYPR_THEME=cyberpunk ./install.sh
```

## How theming works

Three symlinks drive the active look:

| Symlink | Points to |
|---|---|
| `~/.config/hypr/hypr.conf` | `~/.config/themes/<hypr-theme>/hypr.conf` |
| `~/.config/waybar/config.jsonc` | `~/.config/themes/<bar-theme>/waybar.jsonc` |
| `~/.config/waybar/style.css` | `~/.config/themes/<bar-theme>/waybar.css` |

`hyprland.conf` sources `theme.conf` (shared base) and `hypr.conf` (theme-specific, keybinds, etc.).

Switch theme at runtime:
```bash
./switch-theme.sh berserk      # waybar + hypr both if files exist
```

## Waybar popup dropdowns

GTK3 layer-shell popups written in Python (`scripts/popup_*.py`). Each one:

- Toggles via PID file — click widget (or hotkey) to open/close
- Animates in from top (ease-out-cubic, 220ms)
- Animates out upward + fades opacity (160ms), including SIGTERM path
- Position centered on cursor via `hyprctl cursorpos`

| Popup | Hotkey | Bar widget |
|---|---|---|
| Power | Super+Shift+P | ⏻ |
| Network | Super+Shift+N | NET widget |
| Audio | Super+Shift+A | VOL widget |
| Sysinfo | Super+Shift+I | CPU/MEM widget |
| Clock | (click clock) | HH:MM |

Popup scripts use `iwctl` (not NetworkManager) and `wpctl`/`pactl` for audio.

## Syncing changes

When you edit configs live (e.g., tweak waybar CSS in `~/.config/themes/berserk/`):

```bash
cd ~/dotfiles
./sync.sh          # copies live → repo
git diff --stat    # review
git add -A && git commit -m "..." && git push
```

## Dependencies

| Package | Purpose |
|---|---|
| `hyprland` | WM |
| `waybar` | Status bar |
| `python-gobject` | GTK3 popup scripts |
| `gtk-layer-shell` | Layer-shell protocol for popups |
| `kitty` | Terminal |
| `swww` | Wallpaper daemon |
| `iwctl` / `iwd` | WiFi (NetworkManager not used) |
| `pipewire` + `wireplumber` | Audio (`wpctl`/`pactl`) |
| `ttf-jetbrains-mono-nerd` | Font |
| `jq` | Used in some scripts |
| `grim` + `slurp` + `wl-copy` | Screenshots |

## Machine-local overrides

`hyprland.conf` is the only file that should differ between machines (monitor layout, input device names). Everything else is portable. Keep machine-specific bits there and avoid committing them if they're too specific.
