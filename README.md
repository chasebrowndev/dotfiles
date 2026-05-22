# dotfiles

Hyprland + Waybar + Kitty rice for Arch Linux. Dark red-on-black cyberpunk aesthetic with animated GTK3 popup dropdowns on the status bar.

## Quick start

```bash
git clone git@github.com:chasebrowndev/dotfiles.git
cd dotfiles
chmod +x install.sh sync.sh switch-theme.sh
./install.sh
```

Then reload:
```bash
hyprctl reload
killall waybar; waybar &
```

## Waybar popups

Clickable widgets drop down from the bar. Each popup has open/close animations and can also be triggered by hotkey.

- **⏻** — Power menu (lock, suspend, reboot, shutdown) — `Super+Shift+P`
- **NET** — Network info + wifi toggle — `Super+Shift+N`
- **VOL** — Volume control — `Super+Shift+A`
- **CPU/MEM** — System stats per-core — `Super+Shift+I`
- **HH:MM** — Full date/time popup

## Themes

Themes live in `.config/themes/`. Switch with:

```bash
./switch-theme.sh berserk
```

Wallpapers are not tracked (too large). Drop `wallpaper.jpg` into `~/.config/themes/<name>/` and set with `swww img`.

## Structure

```
.config/
  hypr/         hyprland + base theme config
  kitty/        terminal config
  themes/       berserk | cyberpunk | eldensote | kaneki
  waybar/
    scripts/    Python bar widgets + popup scripts
```

See `CLAUDE.md` for full technical docs.
