# Control Center gap matrix: System group

Issue: #264 (map #259, strategy #262, source delta `research/cc-debian-arch-delta`, #260). Code-only comparison, no VM capture.

Pages: General (07), Accessibility (08), Appearance (09), Desktop & Dock (11), Displays (12), Spotlight (14), Wallpaper (15). Reference: `~/Downloads/setting-app/*.png` (viewed, not committed).

## Method and limits

- Arch side read: `arch/pkgbuilds/gnome-control-center/overlay/{pulsar.css,css/*.css,shell/,panels/}` and `patches/`. Debian side read: `pulsaros-control-center/overlay-gnome48/`, `patches-gnome48/`, `prepare-assets.sh`.
- The upstream 48 and 51 trees are not in the repo. Panel content that no overlay or patch touches (General rows, Desktop & Dock rows, Displays arrangement, Spotlight locations) is known only from patch context lines and from memory of upstream. Those claims are marked inferred.
- Certain = visible in the cited file. Inferred = depends on how GTK or libadwaita renders the source, or on upstream files not in the repo.
- Fix kind: CSS = `overlay/css/*.css` or `pulsar.css` (Debian gets it free, see below). Patch = small `.blp` or `.ui` patch. Overlay = whole-file C or UI replacement.
- Hide = macOS row or section with no GNOME setting behind it. No widget is added (map #259 rule).

## What carries to Debian by default

- CSS: certain. `prepare-assets.sh:244-264` appends the Arch `pulsar.css` and all `css/*.css` to Debian `style.css`. A CSS fix on Arch lands on Debian with no ticket, if the selector matches the 48 widget tree (selector match on Trixie libadwaita is inferred).
- Hub header: certain. Debian `cc-hub-header.c` is byte-identical to Arch and has its own `cc-hub-header.ui` with the same classes (22 px icon, spacing 14).
- Panel patches 0300, 0500, 0700, 0900, 1700: certain. Each has a `.ui` port in `patches-gnome48/` with the same groups and style classes.
- Not carried: the `background` panel (Appearance and Wallpaper) is an overlay with its own Debian C, `.blp` and `.ui`, and it is stale on Debian (see Appearance).

## Cross-cutting gaps

| # | Gap | Reference | Arch 51 | Debian 48 | Fix | Cert. |
|---|---|---|---|---|---|---|
| X1 | Sidebar order | Appearance, Apple Intelligence, Desktop & Dock, Displays, Menu Bar, Spotlight, Wallpaper | `cc-panel-list.c:371-379`: system, universal-access, background, display, color, multitasking, search, applications, sharing. Desktop & Dock (multitasking) sits after Displays. Extra `color`, `applications`, `sharing` rows. | Same order (`cc-panel-list.c:388-394`) | overlay (`cc-panel-list.c`, both builds) | certain |
| X2 | Sidebar labels | "Spotlight", "Desktop & Dock", "Wallpaper" | No label override in overlay or patches (no match for these strings). Labels come from upstream `.desktop` names (likely "Search", "Multitasking", "Appearance"). | Same | patch or po (label override) | certain that no override exists; upstream text inferred |
| X3 | No Wallpaper sidebar row | Appearance and Wallpaper are two pages | Both live in one `background` panel; `panel_order` has one `background` id | Same | overlay (second sidebar row to the same panel, scrolled to the wallpaper group) or split the panel | certain |
| X4 | Switch metrics defined per panel | wide pill switch, accent when on, white knob | `css/display.css` and `css/multitasking.css` each define the pill. Other panels (Spotlight, Accessibility) get stock libadwaita switches. | Same CSS | CSS (move once into `pulsar.css`, scope to the content pane) | certain for the duplication; stock look elsewhere inferred |
| X5 | Page title for hero pages | General shows no bar title, only the hero | `cc-window.c:564` adds `pulsar-page-title` to the adopted title on every page, so General likely shows "General" in the bar and in the hero | Debian `cc-window.c` differs (1180 vs 1074 lines), not diffed here | overlay (`cc-window.c`) | inferred |
| X6 | Row icon style | colored glyph on gradient squircle | white symbolic 16 px glyph on a flat squircle (`pulsar.css .pulsar-squircle`, `css/accessibility.css`) | Same | CSS for flat colors; overlay to use the `icons/` set | certain |

## General (07)

Reference: hero card (100 px gray squircle, bold title, centered description), then separate cards of icon rows with chevrons: About, Software Update, Storage / AppleCare / AirDrop / AutoFill, Date & Time, Language & Region, Login Items, Sharing, Startup Disk, Time Machine / Device Management / Transfer or Reset.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Hub header | Hero, centered | Patch 0300: `CcHubHeader hero: true`, gray `#8C8C8C`, centered text, 100 px squircle with 56 px glyph (`cc-hub-header.c:98-109`, `pulsar.css .hero`) | Same, in `cc-system-panel.ui` | Structure matches. Reference title is larger than the 22 px hero title. | CSS (`.hero .pulsar-hub-title` size) | inferred for size |
| Row cards | Several cards by purpose, colored squircle on each row | Patch 0300 adds only the header group. Upstream rows (`region_row` and others) stay in upstream groups. No `css/system.css`, no `pulsar-*` row classes on this panel. | Same | No squircle icons, grouping differs from macOS | patch (style classes and group split, reuse the `pulsar-ua-row` pattern) plus CSS (new `css/system.css`) | certain that no styling exists; upstream row content inferred |
| Row content | macOS-only rows | GNOME has About, Date & Time, Region & Language, Users, Remote Desktop, Secure Shell (only `region_row` is confirmed from the patch; the rest is inferred) | Same, possibly fewer at 48 | AppleCare, AirDrop, AutoFill, Login Items, Startup Disk, Time Machine, Device Management: hide. Software Update, Storage: only if upstream has the row. | none (hide) | inferred |
| Chevrons, separators | Chevron on each row, inset separators | Shared `pulsar.css` separators inset 20 px; `show-arrow` rows get the libadwaita chevron | Same | None | n/a | inferred |

## Accessibility (08)

Reference: non-hero header (40 px blue icon, title, description, blue "Learn more..." link), then Vision, Hearing, Motor sections, each a card of colored-squircle rows with chevrons.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Hub header | icon, title, description, link | Patch 0500: `CcHubHeader`, blue, link `help:gnome-help/a11y` | Same | None | n/a | certain |
| Accessibility menu switch | not present | Patch 0500 keeps the `show_ua_menu_row` group between the header and Vision | Same | Extra switch card before Vision (GNOME-only setting) | patch (move group to the end) | certain |
| Vision | VoiceOver, Zoom, Hover Text, Display, Motion, Read & Speak, Audio Descriptions | Seeing and Zoom (`pulsar-ua-dark`) | Same | 5 of 7 rows have no GNOME panel: hide. Titles differ. | none (hide) | certain |
| Hearing | 5 rows, first is blue | One row, Hearing, `pulsar-ua-red` | Same | Reference first row blue, Arch red. Others: hide. | CSS (class color) | certain |
| Motor | Voice Control, Keyboard, Pointer Control, ... | Typing and Pointing and Clicking, both blue | Same | Reference Keyboard row is gray, not blue. Others: hide. | CSS | inferred (only first rows visible) |
| Row icons | colored squircle | 28 px squircle, 7 px radius, white 16 px glyph, 3 colors (dark, red, blue) in `css/accessibility.css` | Same | Reference also uses green and gray | CSS (add classes) | certain |
| Section headings | bold, about 22 px | 21 px bold, 55 px above (`pulsar.css`) | Same | Close match | n/a | certain |
| Sub-pages | not captured | `css/accessibility.css` covers the main page only | Same | Out of scope (map: sub-pages not specified) | n/a | certain |

## Appearance (09)

Reference: one card with Auto/Light/Dark tiles and Liquid Glass Clear/Tinted tiles; Theme (Color swatches with Multicolor first, Text highlight color, Icon & widget style tiles, Folder color); Windows (Sidebar icon size, Tint window background, scroll bar radios).

Arch panel is `overlay/panels/background/cc-background-panel.{blp,ui,c}` plus `css/appearance.css`. Groups in blp order: Appearance, Liquid Glass, Control Centre, Theme, Wallpaper & Live Wallpaper, Spotlight & App Launcher, macOS Layout & Keyboard Remap, macOS-style Windows & Fullscreen, Mouse & Trackpad Cursors, Notch, Shell Layout & Desktop.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Appearance tiles | Label "Appearance" left in the card, 3 tiles right-aligned, selected tile has a blue ring and bold caption | Group heading "Appearance" above the card; tiles in a centered 440 px clamp grid (3 columns, 24 px gap); ring 3 px accent (`css/appearance.css`); all captions at 70% opacity, selected not bold | Stale: only Light and Dark tiles, no Auto (blp first toggle is labelled "Light"); sets no `gtk-theme` key | Heading outside the card, centered not right-aligned, selected caption not bold. Debian lacks the Auto tile. | CSS (bold caption); overlay (layout); Debian overlay re-sync (Auto tile) | certain |
| Liquid Glass | Label and description left, Clear and Tinted preview tiles | `SwitchRow` "Liquid Glass Effect", `ComboRow` "Liquid Glass Style" (New or Classic), "Extension Settings" button row | Same rows | Rows, not preview tiles. Clear and Tinted do not map to New or Classic: product decision. | overlay (tile widget in `.blp`, `.ui`, `.c`) | certain |
| Theme: Color | Label left, 9 swatches (Multicolor, blue, purple, pink, red, orange, yellow, green, gray), about 48 px, selected name under the swatch | `ActionRow` "Accent Color" with 28 px swatches (36 px with margin), GSettings enum order (blue, teal, green, yellow, orange, red, pink, purple, slate), hover scale 1.15 with shadow, 2.5 px accent ring | Same structure, legacy colors (`#3584e4`, `#3a944a`, `#e66100`, ...) plus a `maia` swatch | Order, size, hover effect, no Multicolor, extra teal, no caption. Debian also has the wrong palette. The swatch CSS is a string in the `.c` file, not a stylesheet. | overlay (`.c`: order, size; move the rules into `css/appearance.css`); Debian port also replaces the palette | certain; order inferred from the enum loop in `setup_accent_color_toggles` |
| Text highlight color | popup row | none | none | No GNOME setting: hide | none | certain |
| Icon & widget style | 4 tiles: Default, Dark, Clear, Tinted | `ComboRow` "Icon Theme" with two Spanish strings in the model ("macOS Tahoe (Predeterminado)", "macOS 27 (Nuevo)") | Same | Combo not tiles; Spanish strings inside an English blp; 2 choices not 4 | overlay (tiles) or patch (strings only) | certain |
| Folder color | popup row | none | none | No GNOME setting: hide | none | certain |
| Windows (icon size, tint, scroll bars) | 3 cards | none | none | No GNOME setting: hide | none | certain |
| Extras (Control Centre, launcher, remap, fullscreen, cursors, notch, shell layout) | not in reference | 8 extra groups after Theme, blue `suggested-action` buttons, group descriptions | Same | Page much longer than the reference. These are Pulsar settings, so keep them, but they carry no Pulsar styling. Decision: leave, move to a sub-page, or reorder. | overlay (reorder) | certain |
| Group descriptions | none outside cards | `description:` text under headings (Liquid Glass, Control Centre, ...) | Same | Reference has none | patch or overlay (drop descriptions) | inferred |

## Desktop & Dock (11)

Reference: Dock (size and magnification sliders, position, minimize animation, double-click action, minimize into icon), auto-hide group, Desktop & Stage Manager, Widgets. All macOS Dock settings.

Panel `multitasking` on both builds. Patch 0900 adds only the class `pulsar-multitasking`. `css/multitasking.css` styles subtitles, switches, radios, checks and the spin row. Upstream content (inferred from patch context and CSS selectors): "Screen Edges" group (hot corner, active edges), Workspaces (dynamic or fixed, count), Multi-Monitor, App Switching.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Page content | Dock, Stage Manager, Widgets rows | Hot corner, edges, workspaces rows | Same | Almost no row maps. Dock, minimize animation, Stage Manager, Widgets: hide. | none (hide) | inferred (upstream rows not in repo) |
| Switches | wide pill, blue on | 46x28 pill, accent, white knob | Same | None | n/a | certain |
| Rows, separators, headings | 38 px rows, inset separators, 21 px headings | shared `pulsar.css` | Same | None | n/a | certain |
| Radios and checks | rounded-square blue checks | accent-filled radios and checks (`css/multitasking.css`) | Same | Radio rows (Dynamic or Fixed) look unlike the reference checks | CSS | inferred |
| Popup rows | gray round chevron badge | shared combo badge (`pulsar.css`) | Same | None, if `image.dropdown-arrow` exists on 48 | n/a | inferred for 48 |
| Sliders | blue track, white thumb, Small/Large labels | shared slider CSS | no slider row | None | n/a | inferred |
| Sidebar position | before Displays | after Displays | Same | See X1 | overlay | certain |

## Displays (12)

Reference: monitor illustration and name, Larger Text to More Space resolution tiles, brightness slider with sun icons, auto-brightness and True Tone switches, Preset, Refresh rate and TV popups each in its own card, buttons Advanced, Night Shift, help.

Arch patch 1700 plus `css/display.css`. Debian patch 1700 is a faithful `.ui` port (same group split).

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Monitor preview | laptop image and name | upstream arrangement widget, untouched | Same | Different widget; no CSS in the repo touches it | CSS (frame) or skip | inferred |
| Resolution | 5 preview tiles with captions | `ComboRow` "Resolution" | Same | Combo not tiles; needs a new widget | overlay (large, own ticket per #262) | certain |
| Card split | Preset, Refresh rate, TV each in its own card | Patch 1700 moves orientation, HDR and underscan into a second `other_listbox`. The first listbox still holds resolution, refresh, HDR brightness and scale. `css/display.css` says rows "read as separate cards" but its rule only sets `margin-bottom: 2px`. | Same | One card for resolution, refresh and scale instead of one card per row | patch (split `enabled_listbox` in `.blp` and `.ui`) | certain |
| Brightness | slider with sun icons | none in this panel | none | No row in the panel (brightness is a shell setting): hide | none | certain (no brightness row in patch context); upstream inferred |
| Auto brightness, True Tone, Preset | switches and popup | none | none | Hide | none | inferred |
| Scale | not shown | `ActionRow` "Scale" with toggle buttons | Same | Extra GNOME row | none | certain |
| Switches, subtitles | pill switch, gray help text | `css/display.css` | Same | None | n/a | certain |
| Footer buttons | Advanced, Night Shift, help | Night Light lives elsewhere in upstream | Same | Position and style differ | patch | inferred |

## Spotlight (14)

Reference: header card (icon, title, description, blue link), a switch card with description and link, two button rows, a "Help improve" switch card, then "Results from Apps" (title and description inside the card, rows with 28 px app icons and switches).

Patch 0700 (hub header, `pulsar-spotlight` class, group retitled "Results from Apps") and `css/spotlight.css`.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Hub header | icon, title, description, link | `CcHubHeader` titled "Search", link `help:gnome-help/shell-apps-open` | Same | Title "Search" vs "Spotlight" (see X2) | patch (title string) | certain |
| Switch cards | Show Related Content, Help Improve Search | `app_search_row` switch group; upstream also has a Search Locations row | Same | Apple items: hide. App Search card exists. | none | certain |
| Reset Quick Keys, Delete Search History | button rows | none | none | No GNOME setting: hide | none | certain |
| Results from Apps | title and description inside the card, no heading above | `search_group` title renders as a 21 px bold heading above the card (`pulsar.css` heading rule), description below it | Same | Heading sits outside the card | patch or overlay (move title into a card header row; CSS cannot move it) | certain for the heading rule; fix inferred |
| App rows | 28 px icon, name, switch, no drag handle, separator starts after the icon | 24 px icons with 6 px radius; drag handle at 35% opacity (`css/spotlight.css`) | Same | Icon 24 vs 28 px; handle visible; separator inset differs | CSS | certain |
| Switches | wide pill | stock libadwaita (no switch rule in `css/spotlight.css`) | Same | Not pill-styled like Displays and Desktop & Dock | CSS (X4) | inferred |

## Wallpaper (15)

Reference: current-wallpaper preview, a card with name and Fill Screen popup and a "Show on all Spaces" switch, buttons Screen Saver and Clock Appearance; below, horizontal carousels per category (Dynamic, Your Photos with an Add Photo tile, Landscape, Cityscape, Underwater), each with a bold title, a "Show All (n)" link and 215x140 tiles with captions and download or video badges.

Arch (`background` panel): group "Wallpaper & Live Wallpaper" with a flat "Add Picture..." header button, a Choose Video and Stop row, a card holding one `CcBackgroundChooser` flowbox, a download row, a legal notice row. `css/appearance.css` styles the flowbox tiles.

| Section | Reference | Arch 51 | Debian 48 | Gap | Fix | Cert. |
|---|---|---|---|---|---|---|
| Page entry | own sidebar row | none (X3) | none | No Wallpaper page | overlay | certain |
| Current wallpaper preview | large preview left, controls right | none in the blp | none | Missing layout | overlay | certain |
| Fit and spaces | popup "Fill Screen", "Show on all Spaces" | none | none | No such GNOME setting: hide | none | certain |
| Screen Saver, Clock Appearance | buttons | none | none | Hide | none | certain |
| Category carousels | one row per category, horizontal scroll, "Show All (n)" | single flowbox card (`background-flowbox`), no categories, no Show All | Single flowbox | No categories; needs a `CcBackgroundChooser` change | overlay (large) | certain |
| Tiles | 215x140, caption below, radius about 10, outline only when selected | flowbox child padding 3, selected 3 px accent outline, thumbnail radius 8, no captions | Same | Size, captions and badges missing; radius 8 vs about 10 | CSS (radius, size); overlay (captions, badges) | certain for radius and outline; size inferred |
| Add Photo | tile in "Your Photos" | "Add Picture..." flat button in the group header | Same | Different control and place | patch | certain |
| Live wallpaper, download, legal rows | not in reference | present, `suggested-action` and `destructive-action` buttons | Same | Pulsar extras: keep and restyle or move | patch (button classes); overlay (placement) | certain |
| Group heading | no page title group | 21 px heading plus description | Same | Drop the description | patch | inferred |

## Debian column summary

| Page | Debian status vs Arch | Debian-specific work |
|---|---|---|
| General | Same patch 0300, same hero | CSS free. Row styling is a patch pair (Arch, then a Debian `.ui` port). Debian keeps the upstream 48 row layout (strategy #262). |
| Accessibility | Same patch 0500 | CSS free |
| Appearance | Stale overlay: no Auto tile, legacy accent palette, extra `maia` swatch | Re-sync the Debian `background` overlay (C, `.blp`, `.ui`) with Arch before any Arch fix ports. `prepare-assets.sh:279-288` overwrites each `.ui` from its `.blp` and swallows compile errors (`\|\| true`), so fix both together. |
| Desktop & Dock | Same patch 0900 | CSS free |
| Displays | Same patch 1700 | CSS free. The card split needs a `.ui` port. |
| Spotlight | Same patch 0700 | CSS free |
| Wallpaper | Same stale overlay as Appearance | Same re-sync. Carousel work goes Arch first. |

## Suggested slicing (input to the map, not a plan)

1. CSS only (Arch, reaches Debian): X4 switch pill, accessibility colors, Spotlight icon and handle, hero title size, wallpaper tile radius.
2. Small patches (Arch plus Debian port): General rows and group split, display card split, Spotlight title, label overrides (X2).
3. Overlay: sidebar order and Wallpaper row (X1, X3), Appearance layout and swatches, Liquid Glass tiles (needs a product decision), Wallpaper carousels and preview (large).
4. Debian prerequisite: re-sync the `background` overlay with Arch.

## Open questions

- Liquid Glass: map Clear and Tinted onto New and Classic, or keep rows? (Product call.)
- Pulsar extras on Appearance (8 groups): keep on the page, move, or use a sub-page?
- Confirm "hide" for AirDrop, Time Machine, Stage Manager, brightness, folder color and the other rows marked hide.
- Check upstream 48 and 51 `.blp` and `.ui` (system, multitasking, display, search) before building; they are not in the repo.
