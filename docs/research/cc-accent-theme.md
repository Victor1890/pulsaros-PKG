# Accent color and theme support (GNOME 51 + MacTahoe)

Research for #51 (child of #48). Question: can a custom Appearance panel drive `accent-color` and Auto/Light/Dark, and what does `pulsaros-theme` define versus the macOS accent set?

Sources: installed `gsettings-desktop-schemas 51.0-1` schemas in `/usr/share/glib-2.0/schemas/`; libadwaita source (installed 1.10.0, `src/adw-accent-color.c` identical at tag `1.10.0` and `main`), `doc/css-variables.md`; MacTahoe fork `Inled-Pulsar-OS/MacTahoe-gtk-theme` @ `6537483`; local files under `pulsaros-theme/`, `pulsaros-gnome/`, `pulsaros-control-center/overlay-gnome48/`.

## 1. GSettings keys (answer: yes, both exist)

Schema `org.gnome.desktop.interface` (`org.gnome.desktop.interface.gschema.xml`, enums in `org.gnome.desktop.enums.xml`):

| Key | Type | Values | Default |
|---|---|---|---|
| `accent-color` | enum `GDesktopAccentColor` | blue(0) teal(1) green(2) yellow(3) orange(4) red(5) pink(6) purple(7) slate(8) | `blue` |
| `color-scheme` | enum `GDesktopColorScheme` | default(0) prefer-dark(1) prefer-light(2) | `default` |

- Exactly nine accents. No `multicolor`, no `graphite`, no custom hex.
- `color-scheme` has no "Auto by time of day" value. `default` means "no preference" (apps render light); `prefer-light`/`prefer-dark` are explicit. A macOS-style Auto/Light/Dark segmented control must map: Auto -> `default` (or a Pulsar-owned sunrise/sunset switcher writing the key), Light -> `prefer-light`, Dark -> `prefer-dark`.
- libadwaita consumes both: `AdwStyleManager` has `accent-color`, `accent-color-rgba`, `system-supports-accent-colors` (since 1.6) and generates `@define-color accent_bg_color <rgba>; accent_fg_color white;` at runtime (`adw-style-manager.c`, `generate_accent_css`). Apps follow live changes through `notify::accent-color`.
- Standalone accent text color (`--accent-color`) is derived automatically in OKLab for light/dark (`doc/css-variables.md`); only `--accent-bg-color` needs overriding.

## 2. libadwaita accent palette (background colors, fg is white)

From `adw_accent_color_to_rgba` (`src/adw-accent-color.c`):

blue `#3584e4`, teal `#2190a4`, green `#3a944a`, yellow `#c88800`, orange `#ed5b00`, red `#e62d42`, pink `#d56199`, purple `#9141ac`, slate `#6f8396`.

## 3. What Pulsar already ships

- Control Center overlay (`panels/background/cc-background-panel.c`): already reads/writes `accent-color` via `g_settings_set_enum` with nine swatches, plus a tenth non-schema `maia` (`#16a085`) swatch class. Its hexes for yellow `#e5a50a`, orange `#e66100`, red `#e01b24` are the older GNOME 42-47 values and differ from libadwaita 1.10 (section 2). Scheme control is two toggles (Default / Dark) writing `default` or `prefer-dark`; no `prefer-light`.
- `pulsaros-gnome/usr/bin/pulsar-sync-accent`: watches `accent-color|color-scheme|gtk-theme`, copies MacTahoe GTK4/GTK3 CSS into `~/.config`, then prepends `@define-color accent_*`, `theme_selected_*`, `selected_*` using the same old-GNOME hex table (so yellow/orange/red also differ from libadwaita). Hardcodes `MacTahoe-blue-*` icon theme regardless of accent.
- `pulsaros-theme/usr/bin/pulsaros-theme-daemon` and `mactahoe-theme-apply`: switch `gtk-theme` MacTahoe-Light/Dark and `gtk-application-prefer-dark-theme` from `color-scheme`; `prefer-dark` -> Dark, else Light. The daemon calls `pulsar-sync-accent --once` after each switch.
- `pulsaros-theme/prepare-assets.sh` (lines ~70-125): after building MacTahoe it deletes all `@define-color accent_*`, replaces `#0088FF` with `@accent_bg_color`, and prepends fallback `#3584e4` definitions, so the theme's own blue becomes accent-driven.

## 4. MacTahoe palette (`src/sass/_colors-palette.scss`, `_colors.scss`)

Normal set (`$theme_color_*`): default `#0088FF`, blue `#2E7CF7`, purple `#9A57A3`, pink `#E55E9C`, red `#ED5F5D`, orange `#E9873A`, yellow `#F3BA4B`, green `#79B757`, grey `#8C8C8C`. (A Nord set also exists; irrelevant.)

Surfaces (libadwaita mapping, `src/sass/gtk/_colors-libadwaita.scss`; values from `_colors.scss`):

| Token | Light | Dark |
|---|---|---|
| `window_bg_color` (`$bg_color`) | `#f5f5f5` | `#333333` (darker variant `#282828`) |
| `view_bg_color` / `card_bg_color` (`$base_color`) | `#ffffff` | `#242424` (darker `#1f1f1f`) |
| `window_fg_color` (`$text_color`) | `#363636` | `#dadada` |
| `sidebar_bg_color` | `#fefefe` | `#333333` (darker `#282828`) |
| borders | `rgba(0,0,0,.08)` | `rgba(255,255,255,.12)` |

Accent is compiled in at build time per `-t` option (one theme per accent). With the prepare-assets patch, accent becomes dynamic instead.

## 5. Gaps versus the macOS set

macOS set (from the reference screenshots, not a primary source verified here): multicolor, blue, purple, pink, red, orange, yellow, green, graphite.

| macOS | GSettings equivalent | Notes |
|---|---|---|
| blue | `blue` | MacTahoe default `#0088FF` vs libadwaita `#3584e4`: visible mismatch |
| purple, pink, red, orange, yellow, green | same-named | Hues differ from MacTahoe `$theme_color_*`; teal has no macOS counterpart |
| graphite | `slate` (`#6f8396`) closest | MacTahoe `grey` is `#8C8C8C`, more neutral |
| multicolor | none | macOS "multicolor" means default blue controls plus per-app tints; no schema value. Treat as `blue` plus a Pulsar-only marker, or drop |
| teal | `teal` | Extra versus macOS; hide or keep |

## 6. Findings and recommendations

1. Panel can drive native keys: `accent-color` and `color-scheme` are stable GSettings; no new schema is required. Already half-implemented in the overlay.
2. Palette is not unified: three different tables exist (libadwaita 1.10, old GNOME hex in the overlay and `pulsar-sync-accent`, MacTahoe). Pick one source of truth. For a macOS look, use MacTahoe `$theme_color_*` values for swatches and also for `pulsar-sync-accent` injection; libadwaita apps will still render their own palette only if no `@define-color` override is present, which `pulsar-sync-accent` supplies.
3. Auto/Light/Dark: add `prefer-light` handling (currently missing) and decide what Auto does (`default` vs scheduled).
4. Multicolor has no backing key; graphite maps to `slate` (or a Pulsar-only value). Anything beyond the nine enum nicks needs a custom key (for example `org.gnome.desktop.interface` cannot be extended; use a Pulsar schema) and a CSS-based swatch.
5. Fix `pulsar-sync-accent` icon theme hardcode and the stale hex table when the palette is chosen.
