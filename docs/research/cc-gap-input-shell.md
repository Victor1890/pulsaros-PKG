# Control Center gap matrix: Input and devices, plus window shell

Issue: #267 (map #259). Strategy from #262: Arch 51.1 leads, Debian 48 ports it and keeps the upstream 48 layout where widget trees differ (CSS only unless the gap is large).
Evidence is code only, no VM capture. Upstream 48 and 51 trees were not available, so upstream widget structure is inferred from what our overlay and patches touch. Screenshots viewed: `28-Keyboard`, `29-Trackpad`, `30-Printers-Scanners` (macOS 26, dark). Every screenshot shows the same window shell.

Legend. Certainty: **certain** (read straight from source or reference) or **inferred** (rendered look deduced). Fix kind: **CSS** (`pulsar.css` or `css/*.css`, shared by both builds), **patch** (numbered `.patch`, one per distro), **overlay** (whole-file `.blp`/`.ui`/`.c` replacement), **omit** (no GNOME panel or setting, add nothing), **none** (already matches).

Paths: `A` = `arch/pkgbuilds/gnome-control-center/`, `D` = `pulsaros-control-center/`.

## Answer in brief

1. Shell: Arch already matches the reference on fixed 270 px sidebar, search pill, profile row, left traffic-light layout, accent-filled selected row, back/forward capsule and bold left title. The gaps are visual details (floating rounded sidebar, capsule outline and divider, header hamburger menu, window-control art) and all are CSS or small C.
2. Debian shell is closer to Arch than the reference README says: `D/overlay-gnome48/shell/cc-window.c` builds the capsule, menu button and `pulsar-page-title` in C, so Debian has the capsule (the README line "Debian has no back/forward capsule" is stale). Shell CSS is shared.
3. Keyboard: Arch order and headings match (Keyboard Shortcuts first, "Text Input" heading). Most reference rows have no GNOME equivalent (key repeat sliders, backlight, globe key, dictation) and are omitted. **Debian bug, certain:** patch `0800` nests every later group inside the first one.
4. Trackpad: the real gap is structure, not styling. GNOME uses `CcSplitRow` illustration rows and device-type tabs in the header bar; the reference uses popup rows and a segmented control inside the page. Slider styling is already done on Arch; Debian lacks the `width-request: 300` Arch adds.
5. Printers: status dot, pill add button and default-printer outline are done on both. Remaining gaps are the "Default printer / Default paper size" card (omit), the "Printers" heading and the chevron row (patch, inferred).

## 1. Window shell (all 30 screenshots)

| # | Element | Reference shows | Arch 51 (source) | Debian 48 (source) | Gap | Cert. | Fix |
|---|---|---|---|---|---|---|---|
| S1 | Window frame | One rounded window, traffic lights top-left inside sidebar | `A/overlay/shell/cc-window.blp:5-6` 980x640; sidebar headerbar `decoration-layout: "close,minimize,maximize:"` (`:35`) | Same in `D/overlay-gnome48/shell/cc-window.ui:3-5,28-31` | Layout matches | certain | none |
| S2 | Traffic-light art | Red, yellow, green discs, about 14 pt, 46 px pitch at 2x | No `windowcontrols` rule in any overlay CSS. Look comes from the user theme `pulsaros-gnome/usr/share/pulsar-dots/blocks/gtk4.css` (PNG backgrounds via `@HOME@/.local/share/pulsar-dots/*.png`, 15 px) | Same dependency | Control Center ships no window-control styling; without the pulsar-dots gtk.css the buttons are stock Adwaita grey. Not testable by code | inferred | out of CC scope (theme); optional CSS in `pulsar.css` scoped to `.cc-sidebar-pane windowcontrols` for both builds |
| S3 | Sidebar surface | Floating inset rounded panel (about 8 pt margin, about 20 pt radius), darker than page, window colour visible around it | `pulsar.css:40-47` sets sidebar colour on `.cc-sidebar-pane`; no margin, no radius, so a full-height flat column | `cc-sidebar-pane` class present in `.ui:20-22`, same CSS | Sidebar is flush with the window edge, not a floating card | inferred | CSS (`.cc-sidebar-pane` margin plus radius plus `overflow: hidden`); Debian inherits |
| S4 | Sidebar width | Sidebar about 30 percent of window | Fixed 270 px of 980 (`cc-window.blp:19-20`), 27.5 percent | Same 270 (`.ui:15-16`) | Close; about 3 points narrower | inferred | none (optional 290) |
| S5 | Search pill | Full-width pill, magnifier left, "Search" placeholder, about 28 pt | `entry.pulsar-search-pill` radius 999, min-height 28 (`pulsar.css:27-30`); margins 12/6 (`cc-window.blp:41-45`) | Same class and margins (`.ui:35-46`) | Matches | certain | none |
| S6 | Profile row | 40 pt avatar, bold name, grey "Apple Account" caption | `Adw.Avatar` 40, `heading` name, `caption dim-label` "Local Account" (`cc-window.blp:63-88`) | Same (`.ui:56-96`) | Matches in structure; sub-label text differs (account name is data) | certain | none |
| S7 | Sidebar rows | 32 pt pitch, 20 pt squircle icon, gradient glyph icons per app | 32 px row, 8 px radius (`pulsar.css:50-58`); 24 px flat-colour squircle with a 16 px glyph (`cc-panel-list.c:245-255`), colours per id (`pulsar.css:136-186`) | `D/overlay-gnome48/shell/cc-panel-list.c:915` same metrics, same classes | Icons are flat fills not gradients; 24 px vs about 20 pt. Colours for Input rows are right (keyboard, mouse, printers grey `#8C8C8C`, `pulsar.css:150-158`) | inferred | CSS (gradient fills) or overlay (use `A/icons`); Debian has no `icons/` dir, so icon art is an overlay copy |
| S8 | Sidebar selected row | Solid accent rounded rect, white text | `pulsar.css:76-84` | Shared CSS | Matches | certain | none |
| S9 | Sidebar groups | Spacing only, six groups | `panel_order[]` identical in both builds: connectivity, general, alerts, security, hardware (`A/.../cc-panel-list.c:360-400`, `D/.../cc-panel-list.c:377-417`) | Identical | Group split differs from macOS (apps, sharing, wacom, reset-settings, color shown; VPN, Lock Screen, Touch ID, Internet Accounts, Wallet not). Belongs to the sidebar-order tickets, not this one | certain | overlay (`cc-panel-list.c`), hide rows via visibility; both builds |
| S10 | Content header | Back/forward capsule left, bold title, nothing on the right | Capsule `box.linked.pulsar-nav-capsule` (`cc-window.blp:116-139`); title `pulsar-page-title` 28 px bold (`pulsar.css:213-217`; `cc-window.c:561-570`). Menu button at `[end]` (`:141-147`) | Capsule, title and menu button built in C (`D/.../cc-window.c:1089-1122`, `:597-620`); `.ui` has no content header, content set in C (`cc-window.c:166`) | Capsule exists on both. **Hamburger menu present, reference has none** | certain | overlay (`cc-window.c`: stop adopting `main_menu_button`; keep Shortcuts/Help/About reachable elsewhere or drop). Debian same C change |
| S11 | Capsule look | One outlined pill, about 36 pt tall, chevrons, 1 px divider between buttons | Fill only `alpha(currentColor,0.07)`, 28 px buttons, `linked` removes the divider (`pulsar.css:111-122`) | Shared CSS | No outline, no divider, shorter | inferred | CSS (border, divider, min-height 36) |
| S12 | Title size | About 17 pt bold | 28 px (`pulsar.css:213-217`), about 20 px if scaled to the 980 px window | Shared | Likely about 25 percent too large | inferred | CSS (`font-size`) |
| S13 | Page surface | Page slightly lighter than window, cards lighter again (dark mode) | `.content-pane` uses `@view_bg_color`, cards `@card_bg_color` (`pulsar.css:92-111`) | Shared | Dark matches. Light mode: libadwaita light view and card are both near white so cards may vanish (the comment says "light-grey cards" but code uses the stock token). No light reference | inferred | CSS (`--card-bg-color` override in light) |
| S14 | Cards, rows, headings | 12 pt radius, hairline inset separators, bold headings | `pulsar.css:128-177` radius 12, rows 38 px, inset 20 px gradient separators, 21 px bold headings | Shared | Matches | certain | none |
| S15 | Combo rows | Round grey up/down chevron badge | `pulsar.css:259-273` for `row.combo` (AdwComboRow only) | Shared | Works only on AdwComboRow; not on `CcSplitRow`, `CcListRow` | certain | CSS (see keyboard K3) |
| S16 | Sliders | Blue track, large round light thumb, ticks, end labels | `pulsar.css:221-257` | Shared | Matches; thumb is white not light grey | inferred | none |
| S17 | Help `?` circle and bottom pill buttons | Round `?` and "Set Up ..." pill at page bottom right | none | none | No GNOME equivalent | certain | omit |

## 2. Keyboard (`28-Keyboard.png`, panel id `keyboard`)

Arch order after patch `0800`: Keyboard Shortcuts, Text Input, Input Source Switching, Special Character Entry (`A/patches/0800-keyboard-text-input-groups.patch`; overlay `.blp` is patched, `A/overlay/panels/keyboard/cc-keyboard-panel.blp`). CSS: `A/overlay/css/keyboard.css` (class `pulsar-keyboard` added by the patch).

| # | Section (reference) | Reference shows | Arch 51 | Debian 48 | Gap | Cert. | Fix |
|---|---|---|---|---|---|---|---|
| K1 | Key repeat rate and Delay until repeat | Card, two sliders side by side, ticks, Off/Slow/Fast and Long/Short | Not in the Keyboard panel. GNOME has repeat keys under Universal Access, Typing (slider marks via patch `0200`) | Patch `0200` ported | No such controls here | certain | omit (the setting lives in another panel) |
| K2 | Backlight card (brightness toggle, backlight timeout, globe key, keyboard navigation) | Switch and popup rows | none | none | No GNOME setting | certain | omit |
| K3 | Keyboard Shortcuts button | Right-aligned grey pill "Keyboard Shortcuts..." at the end of the first card | `CcListRow` "View and Customize Shortcuts" with `show-arrow`, first group (patched `.blp`); `keyboard.css:2-9` turns the arrow into a 28 px round grey badge | Same row, first group (`D/patches-gnome48/0800`), same CSS | Row with round chevron badge, not a grey text pill; heading "Keyboard Shortcuts" is extra (reference has none above the card) | inferred | CSS (pill style on the arrow row) or patch (drop group title) |
| K4 | Text Input heading | Bold heading | Group title "Text Input" (patch `0800`) with description "Includes keyboard layouts and input methods" | Same title and description | Extra description line the reference lacks | certain | patch (remove `description`) |
| K5 | Input Sources row | One row: "Input Sources", value "ABC", pill "Edit..." | `CcInputListBox` (upstream C widget): one row per source with reorder handle, options button and an add row | Same widget, upstream 48 | Different row model: per-source rows and add button vs one summary row plus Edit | inferred | patch or overlay (large; CSS only gets pill buttons). Debian: CSS only per #262 |
| K6 | Text Replacements | Pill button | none | none | No GNOME feature | certain | omit |
| K7 | Special Character Entry (Alternate Characters Key, Compose Key) | not in reference | `CcListRow` with `show-arrow` | Same (`D/.../cc-keyboard-panel.ui`) | GNOME-only; styled with the round badge and grey value via `keyboard.css:11-14` (selector assumes `label.dim-label` inside `box.suffixes`, not confirmed on `CcListRow`) | inferred | keep; verify selector (CSS) |
| K8 | Input Source Switching | not in reference | Two `AdwActionRow` radio rows | Same | GNOME-only; radio prefix looks stock, reference has no radio rows | certain | keep |
| K9 | Dictation card (toggle, languages, microphone, shortcut, auto-punctuation, Ask Siri link) | Whole section | none | none | No GNOME dictation | certain | omit |
| K10 | Page structure (Debian only) | Separate cards under bold headings | n/a | Patch `0800` inserts the new first group but never closes it. Replaying the patch on `overlay-gnome48/panels/keyboard/cc-keyboard-panel.ui` gives valid XML in which Text Input, Input Source Switching and Special Character Entry are children of the Keyboard Shortcuts group, not siblings | Groups nested inside a group: wrong spacing, headings and first-child rules (`pulsar.css:168-171`) | certain (structure, by patch replay); inferred (visible effect) | patch (fix `0800` in `D/patches-gnome48/`, add the closing `</object></child>`) |

## 3. Trackpad (`29-Trackpad.png`, panel id `mouse`)

Both builds ship the whole mouse panel as overlay (`A/overlay/panels/mouse/cc-mouse-panel.{blp,c}`, `D/overlay-gnome48/panels/mouse/cc-mouse-panel.{ui,c}`) plus patch `1500` (slider marks). There is no `css/mouse.css`; styling comes from `pulsar.css` (sliders, rows).

| # | Section (reference) | Reference shows | Arch 51 | Debian 48 | Gap | Cert. | Fix |
|---|---|---|---|---|---|---|---|
| T1 | Preview pair | Trackpad outline with dot plus a looping gesture demo | none | none | No GNOME equivalent | certain | omit |
| T2 | Tab strip | Segmented control inside the page: Point & Click, Scroll & Zoom, More Gestures; selected tab accent-filled | `Adw.ViewSwitcher` in the header bar, policy wide, pages Mouse, Touchpad, Pointing Stick (`.blp:24-50,164,292`); switcher bar at the bottom when narrow | `AdwViewSwitcher` (`.ui:29`) and `AdwViewSwitcherBar` (`:51`); no Pointing Stick page (0 matches) | Switcher sits in the header and is device-type tabs, not feature tabs; stock styling | certain (placement); inferred (look) | CSS (round segmented look, accent fill) for both; moving it into the page is overlay (inferred, small). Debian CSS only |
| T3 | Tracking speed | Label left, slider right, ticks, Slow/Fast | Touchpad "Pointer Speed" `Adw.ActionRow` with `Scale`, 9 marks, `width-request: 300` (`A/patches/1500`) | Same 9 marks, **no `width-request`** (`D/patches-gnome48/1500`); inserted mark lines left unindented | Slider width unset on Debian, so it can shrink to the minimum | certain | patch (add `width-request` to the scales in the Debian `.ui`) |
| T4 | Click (Light/Medium/Firm), Force Click, Look up | Slider and rows | none | none | Hardware feature | certain | omit |
| T5 | Secondary click | Popup row "Click with Two Fingers" with grey chevron badge | `$CcSplitRow two_finger_push_row` (two illustrated options, `.blp:222-231`) | `CcSplitRow` (`.ui:250`) | Large illustrated choice vs a popup row; the combo badge CSS (`pulsar.css:259-273`) never applies | certain (widget); inferred (look) | overlay (swap to `Adw.ComboRow`, adapt `cc-mouse-panel.c`); big, Debian keeps split rows per #262 |
| T6 | Tap to click | Switch row with subtitle "Tap with one finger" | `Adw.SwitchRow` "Tap to Click", subtitle "Quickly touch the touchpad to click" | Same `AdwSwitchRow` | Text only | certain | none |
| T7 | Scroll rows | Natural scrolling in the Scroll & Zoom tab | `CcSplitRow` Scroll Method and Scroll Direction | `CcSplitRow` | Same as T5 | certain | overlay (same as T5) |
| T8 | Group layout | One card, no headings | Several groups with 21 px bold headings: "Touchpad", "General", "Clicking", "Scrolling", "Test Settings" (`.blp:172-290`) | Same groups | More cards and headings than the reference | inferred | overlay (merge groups, drop titles); optional |
| T9 | GNOME-only rows | not in reference | Disable While Typing, Disable While a Mouse Is Connected, Primary Button toggle group, Mouse Acceleration, Test Settings | Same (no Pointing Stick) | Keep | certain | keep |
| T10 | Bottom `Set Up Bluetooth Trackpad...` and `?` | Pill and circle | none | none | No equivalent | certain | omit |

## 4. Printers & Scanners (`30-Printers-Scanners.png`, panel id `printers`)

No overlay panel on either side: only patch `1800` plus `A/overlay/css/printers.css`. Both patches add `pulsar-pill` to the Add button and `update_pulsar_style()` in `pp-printer-entry.c` (status dot class plus `pulsar-default-printer`). The Debian patch is the same C with different line offsets and a `.ui` hunk (`D/patches-gnome48/1800`).

| # | Section (reference) | Reference shows | Arch 51 | Debian 48 | Gap | Cert. | Fix |
|---|---|---|---|---|---|---|---|
| P1 | Default printer / Default paper size | Card with two popup rows | none; GNOME sets the default per printer (the entry's `is_default`) | none | No setting in the panel | certain | omit |
| P2 | "Printers" heading | Bold heading above the list | No group heading in the printers panel (patch context shows only the Add button hunk, `cc-printers-panel.blp:35`) | Same | Heading missing | inferred | patch (title on the list group) |
| P3 | Printer row | One card row: printer glyph, name, green dot plus "Idle, Last Used", chevron | `list.boxed-list-separate > row` per printer, upstream `PpPrinterEntry` (icon, name, status, ink levels, options menu); status dot via `printers.css:11-27` | Same widget and same classes | Dot matches. Upstream row has ink levels and a menu button instead of a chevron; status text differs | inferred | CSS (hide ink bar) or patch (chevron suffix) |
| P4 | Default-printer marker | none (the reference printer is not default) | 2 px accent-coloured outline, hard-coded `#0a84ff` (`printers.css:5-7`) | Same | Extra decoration. Colours hard-coded (`#0a84ff`, `#34c759`) rather than the accent token | certain | CSS (`@accent_bg_color`, or drop) |
| P5 | Add Printer button | Grey pill "Add Printer, Scanner, or Fax..." plus `?` circle at bottom right | `pulsar-pill` (radius 999, 10 percent fill, `printers.css:29-34`) | `pulsar-pill` via the `.ui` hunk | Style matches; label and placement are upstream (placement not confirmed from source). No `?` button | certain (style); inferred (placement) | none for style; omit `?` |

## Debian summary

| Item | Debian status | Action |
|---|---|---|
| Shell CSS (`pulsar.css`, 15 `css/*.css`) | Same file, appended in `prepare-assets.sh` | Free once Arch CSS changes |
| Shell C (`cc-window.c`, `cc-panel-list.c`) | Own copies, differ (1180 vs 1074 and 1121 vs 1005 lines) | Port each Arch C change by hand (S9, S10) |
| Keyboard patch `0800` | Defective nesting (K10) | Debian-only fix |
| Mouse patch `1500` | Missing `width-request` (T3), no Pointing Stick | Debian-only fix |
| Printers patch `1800` | Equivalent | none |
| `CcSplitRow`, `CcInputListBox`, `PpPrinterEntry` | Upstream 48 widgets | Keep per #262; CSS only |

## Suggested ticket slices (for the map)

1. CSS: shell polish S3, S11, S12, T2 tab look, K3 pill, P4 accent colour (Arch; Debian inherits).
2. Patch: Debian `0800` nesting fix K10 and `1500` `width-request` T3 (Debian-only, small, independent).
3. Overlay C: remove the header hamburger (S10) in both `cc-window.c` files.
4. Optional larger: K5 input-source summary row, T5/T7 popup rows, T8 group merge.

## Not verified

- No upstream 48 or 51 source was read. K5, P2, P3, P5 placement rest on what overlays and patches show.
- Light mode was not compared (all references are dark).
- The window-control look depends on files outside the Control Center packages.
- K10 was shown by replaying the patch against the overlay `.ui`; a build was not run.
