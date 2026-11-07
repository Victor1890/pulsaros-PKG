# Control Center 51.1: sidebar, header and styling hooks

Issue: Victor1890/pulsaros-PKG#50 (child of #48). Upstream base: gnome-control-center `51.1`
(`https://gitlab.gnome.org/GNOME/gnome-control-center/-/raw/51.1/<path>`). Libadwaita docs:
`https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/`.

## Short answer

Yes, all four wanted sidebar features are reachable with libadwaita/GTK4 widgets. Two
mechanisms matter most:

1. CSS needs no file replacement: `style.css` in the app resource base path is auto-loaded.
2. The sidebar is a plain `GtkListBox` built in C, so structure (groups, colored icons)
   is changed in `cc-panel-list.c`, which the overlay already replaces.

## What the Arch build actually does today

- `arch/pkgbuilds/gnome-control-center/PKGBUILD` (pkgver 51.1, pkgrel 8) clones upstream tag 51.1,
  then `cp -rf $startdir/overlay/* .` in `prepare()`. The old `pulsar-macos-style.patch` is only a
  fallback if `overlay/` is missing. Icons from `overlay/icons` are installed to
  `hicolor/scalable/apps`.
- The directory `pulsaros-control-center/overlay-gnome48` is the Debian/GNOME 48 copy; it ships
  `cc-window.ui` and no `.blp`, so it is a different upstream generation. Arch uses
  `arch/pkgbuilds/gnome-control-center/overlay`. Only the Arch one matters for #48.
- Arch overlay files under `shell/`: `cc-panel-list.c`, `cc-window.blp`, `cc-window.c`. Whole-file
  replacements of upstream files (the .c files drifted: indentation differs and `cc-panel-list.c`
  is 1044 lines vs upstream 976; diff against 51.1 before editing).
- The overlay already has: a profile row (`Button user_account_banner` with `Adw.Avatar`, name and
  "Local Account" caption, click opens `online-accounts`, in `cc-window.blp` / `setup_user_account_banner()`
  in `cc-window.c`), custom per-panel SVG icons via a long `if (g_strcmp0 (id, ...))` chain
  loading absolute paths, a custom `panel_order` and 24px icons.
- The overlay adds no stylesheet. `grep css` over the overlay `.c` files only finds `dim-label`.

## Upstream structure (51.1)

| Piece | Source | Notes |
|---|---|---|
| Window | `shell/cc-window.blp` | `Adw.ApplicationWindow` > `Adw.NavigationSplitView split_view`; breakpoint `max-width: 550sp` collapses it |
| Sidebar page | same file | `Adw.NavigationPage` > `Adw.ToolbarView`: `[top] Adw.HeaderBar` (search `ToggleButton`, primary menu) + `[top] SearchBar` + `ScrolledWindow` > `$CcPanelList panel_list` |
| Search | same file | `SearchBar search_bar` bound to `search_button.active`; `SearchEntry search_entry`; query bound to `panel_list.search-query` |
| Content | same file | `Adw.NavigationPage` > `Adw.NavigationView navigation` (panels are pushed into it by `cc-window.c`) |
| Panel list | `shell/cc-panel-list.blp` | `Adw.Bin` > `Stack` with page `main` (`ListBox main_listbox`) and `search` (`ListBox search_listbox` + `Adw.StatusPage` placeholder). Both use style `navigation-sidebar` |
| Rows | `shell/cc-panel-list.c` `row_data_new()` | `GtkListBoxRow` > `GtkGrid`: `GtkImage` (icon-name), name label, hidden description label |
| Groups | `cc-panel-list.c` `panel_order[]` + `header_func()` | Groups are the `"separator"` entries of `panel_order`; `header_func` sets a `GtkSeparator` as row header when the previous entry is `"separator"`. `sort_function` orders by index in `panel_order` |
| Registration | `cc-panel-list.c` `cc_panel_list_add_panel()` | called from `cc-window.c` per panel, with `icon` from the panel's desktop file |
| Selection/nav | `cc-panel-list.c` | `row_activated_cb`, `cc_panel_list_set_active_panel`; emits `show-panel` consumed by `cc-window.c` |
| Header/page | `shell/cc-panel.blp` | per-panel page; each panel pushed in the `NavigationView` has its own header bar |
| Resources | `shell/gnome-control-center.gresource.xml.in` | prefix `/org/gnome/Settings/gtk`: `cc-panel.ui`, `cc-panel-list.ui`, `cc-window.ui`, `style.css`; prefix `/org/gnome/Settings`: `style.css`, metainfo, `shortcuts-dialog.ui` |
| Blueprint build | `shell/meson.build` | `ui_sources` list (`.blp`) run through `blueprint-compiler batch-compile` into `.ui`; needs `blueprint-compiler >= 0.19` |
| Versions | top `meson.build` | `libadwaita >= 1.8.alpha`, `blueprint-compiler >= 0.19` |

## Where CSS can be injected without replacing whole files

- `shell/style.css` is listed in the gresource under `/org/gnome/Settings/style.css`. Libadwaita
  documents that `AdwApplication` loads `style.css` from the app resource base path automatically
  ("If there's a resource located at style.css, AdwApplication will load styles from it").
  So the least invasive hook is to append to upstream's `style.css` in `prepare()`:
  `cat "$startdir/overlay/pulsar.css" >> shell/style.css`. No `.c`, `.blp` or gresource edit needed.
  Prefer appending over replacing so the 51.1 rules (e.g. `.accent-button`, `row.split-row`) stay.
- Alternative: add a new file plus a `sed` on `gnome-control-center.gresource.xml.in`. Avoid:
  more moving parts for the same result.
- `style-dark.css` / `style-hc.css` are deprecated in libadwaita; use `@media (prefers-color-scheme: dark)`
  inside `style.css` as upstream does for the bar chart.
- Named colors to override live in `:root` (libadwaita CSS variables page): `--accent-bg-color`,
  `--accent-fg-color`, `--sidebar-bg-color`, `--sidebar-fg-color`, `--sidebar-backdrop-color`,
  `--sidebar-border-color`, `--sidebar-shade-color` (defaults light `#ebebed` / dark `#2e2e32` for bg).
  They apply to `AdwNavigationSplitView` sidebar pane when not collapsed.
- Patch vs. overlay: `prepare()` also supports `patch -Np1`. For small hunks in `.blp`/`.c` a patch
  survives upstream drift better than overlay files; for CSS, `cat >>` is simplest.

## Feature by feature

### Search field at the top of the sidebar
Possible, small change in `cc-window.blp`. Upstream hides the field behind a header toggle
(`SearchBar` + `ToggleButton`). To show it permanently, drop the `SearchBar` wrapper and place
`SearchEntry search_entry` in a `Box` inside the `Adw.ToolbarView` `[top]` area (or as first child of
the sidebar content), and bind `panel_list.search-query` to `search_entry.text` as today. But
`search-mode` is a property of `CcPanelList` (it switches the Stack to `search`), so keep
`search-mode: bind` driven by "entry text is non-empty" instead of `search_bar.search-mode-enabled`.
`search_button` and the `search_bar` references in `cc-window.c` (`search_entry_activate_cb`,
`search_entry_key_pressed_cb`, start-typing capture) must be adjusted, so this touches `cc-window.blp`
and `cc-window.c`. Both are already overlaid.

### Profile row
Already present in the overlay (see above). Gaps: it sits above `[top]` SearchBar in the header
area, uses the strings "Apple ID & Accounts" as fallback, reads GOA `accounts.conf` by hand, and uses
a `flat` Button. No new hook is needed, only restyling and ordering relative to the search entry.

### Grouped sections with colored squircle icons
- Grouping: add titles by extending `header_func` to set a `GtkLabel` (style `heading`/`caption-heading`)
  instead of a bare separator, or insert group-title rows. `panel_order` already encodes groups.
- Squircle: `GtkImage` cannot take a squircle by itself. Wrap the image in a `GtkBox`/`GtkOverlay`
  with a CSS class (for example `.cc-sidebar-icon`) and style `background`, `border-radius`, and
  per-panel color classes (`.cc-icon-wifi { background: ... }`). Libadwaita CSS supports `border-radius`
  on any widget node; a true superellipse is not available, so a large radius (~8px on a 28px box,
  or `border-radius: 30%`) approximates it.
- The overlay today loads full pre-rendered squircle SVGs (`overlay/icons/*.svg`) at 24px with
  `gtk_image_set_from_file` from absolute `/usr/share/icons/...` paths. That works but bypasses the icon
  theme; CSS-colored backgrounds with symbolic glyphs are tunable per theme and need no SVG art.
- Hook files: `cc-panel-list.c` (`row_data_new`, `header_func`) plus CSS.

### Blue selected row
`.navigation-sidebar` is explicit that selected items use a neutral color, not accent (libadwaita
style classes docs; `_sidebars.scss` sets `row:selected { background-color: $selected_color }`).
Override in CSS appended to `style.css`:

```css
.navigation-sidebar row:selected,
.navigation-sidebar row:selected:hover {
  background-color: var(--accent-bg-color);
  color: var(--accent-fg-color);
  border-radius: 8px;
}
```

The selector must be as specific as libadwaita's `.navigation-sidebar row:selected` plus the
`:hover`/`:active` variants listed in `_sidebars.scss`. Scope with a class added to `main_listbox`
(e.g. `cc-sidebar`) in `cc-panel-list.blp` to avoid touching the search list or other panels' sidebars.
Accent blue then follows the user's accent setting (`--accent-bg-color`); to pin macOS blue,
set `--accent-bg-color` on the listbox node.

### Inset rounded cards and header
Panel pages already use `Adw.PreferencesGroup`/`.boxed-list`; per libadwaita, `.boxed-list-separate`
renders each row as its own card and `.card` works on any widget. Header pill (back/forward) is a
`cc-window.blp` / `cc-panel.blp` change (out of this ticket's scope).

## Alternative: AdwSidebar (libadwaita 1.9+)

Libadwaita main docs list `Adw.Sidebar` (since 1.9): sections (`AdwSidebarSection`) of items
(`AdwSidebarItem`), `selected`, `activated` signal, `filter`, `prefix`/`suffix`, `mode` (`sidebar` or
`page` for the collapsed state), `menu-model`. Fits "search on top, grouped sections, selected row"
natively, with titled sections. Cost: a rewrite of `cc-panel-list.c` and `cc-window.blp`, and it needs
libadwaita >= 1.9. The dev host's Arch has `libadwaita 1.10.0`, but upstream 51.1 only requires
`>= 1.8.alpha`, and the ISO's package snapshot version was not verified. Recommend the
`GtkListBox` + CSS route first; revisit `AdwSidebar` only if group titles prove awkward.

## Files that must change (recommended minimal route)

| File | Change | Replace whole file? |
|---|---|---|
| `overlay/pulsar.css` (new) + `PKGBUILD prepare()` | `cat` appended to `shell/style.css` | no (append) |
| `overlay/shell/cc-panel-list.c` | group header labels, wrap icons in colored squircle box, add CSS class to rows/listbox, drop absolute-path SVG loading | already overlaid |
| `overlay/shell/cc-window.blp` | permanent search entry, profile row placement | already overlaid |
| `overlay/shell/cc-window.c` | search wiring for the permanent entry | already overlaid |
| `shell/cc-panel-list.blp` | optional: add style class `cc-sidebar` to `main_listbox` | new overlay file or a 1-line `sed` |

No `meson.build` or gresource edit is required for the CSS route.

## Open points

- The `overlay-gnome48` tree (Debian) is out of scope and diverges (uses `.ui`). Not analysed further.
- Exact squircle shape and per-panel color palette are design decisions for #49/#52.
- The 51.1 diff of overlay `.c` files vs upstream was only skimmed (header, row construction, profile
  banner); other drift may exist.
- Not run: nothing here was built or launched; test loop per `GLOSSARY.md` is the QEMU VM.

## Sources

- gnome-control-center 51.1: `shell/cc-window.blp`, `shell/cc-panel-list.blp`, `shell/cc-panel-list.c`,
  `shell/cc-window.c`, `shell/style.css`, `shell/gnome-control-center.gresource.xml.in`, `shell/meson.build`, `meson.build`.
- libadwaita docs: `style-classes.html` (Sidebars, Boxed Lists), `css-variables.html` (Sidebar Colors),
  `class.Application.html` (Stylesheet), `class.Sidebar.html`.
- libadwaita 1.8.0 `src/stylesheet/widgets/_sidebars.scss` (`.navigation-sidebar` rules).
- Repo: `arch/pkgbuilds/gnome-control-center/PKGBUILD`, `arch/pkgbuilds/gnome-control-center/overlay/shell/*`.
