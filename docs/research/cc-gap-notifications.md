# Control Center gap matrix: Notifications group (Notifications, Sound, Focus, Screen Time)

Issue: #265 (map #259). Strategy: #262 (Arch leads, Debian hand-ports; Debian keeps the upstream 48 layout where widget trees differ, CSS only unless the gap is large). Prior delta: `docs/research/cc-debian-arch-delta.md` (branch `research/cc-debian-arch-delta`, #260).

Evidence is code only, no VM capture. Reference: `~/Downloads/setting-app/16..19` (macOS 26, dark). Sources read:

- Arch: `arch/pkgbuilds/gnome-control-center/overlay/{pulsar.css,css/notifications.css,css/sound.css,css/screen-time.css,panels/sound/*,shell/cc-hub-header.blp,shell/cc-panel-list.c}` and `patches/{0400,0600,1400}-*.patch`.
- Debian: `pulsaros-control-center/overlay-gnome48/panels/sound/cc-sound-panel.{ui,c}`, `overlay-gnome48/shell/cc-panel-list.c`, `patches-gnome48/{0400,0600,1400}-*.patch`, `prepare-assets.sh:244-272`.
- Not available: upstream 48 and 51 trees. The Notifications and Screen Time panel `.blp`/`.ui` exist only as patch hunks, so their upstream structure is inferred. The host has `/usr/share/glib-2.0/schemas/org.gnome.desktop.{notifications,sound}.gschema.xml`, used for key names.

Legend: **certain** = read directly in a repo file or reproduced by applying a patch. **inferred** = depends on upstream code or GTK/libadwaita rendering that was not read. Fix kind: CSS, patch (small edit to an upstream file), overlay (whole-file replacement or new C/UI).

## Answer in brief

- Notifications: hub header, "Notification Center" and "Application Notifications" headings, 20 px card gap, hairlines and round chevron badges are already on both builds. Remaining gaps are content, not style: no "Show previews" popup, no "display is sleeping / mirroring" rows, per-app subtitle shows On/Off instead of "Badges, Sounds, Desktop". GNOME has no setting for most of these, so leave them out.
- Sound: the biggest gap group. mac shows an inline Alert sound popup plus play button, three effect toggles, tick-marked sliders with speaker end icons and an Output|Input segmented table. GNOME has a Volume Levels row, an Alert Sound row, a Startup Sound switch, and separate Output and Input groups. Cheap wins: slider tick marks (patch) and the popup badge on Debian (CSS). The segmented table is overlay-sized.
- Focus: no GNOME panel. Hide (already absent from the sidebar). The only related control is the Do Not Disturb switch, already on the Notifications page.
- Screen Time: GNOME `wellbeing` has Usage, Screen Limit and Break Reminders. mac has four icon-prefixed link lists. Only titles and icon prefixes could match; the rest maps to nothing in GNOME.
- Debian: patch `0400-sound-effects-first` produces a mis-nested tree (certain, see S2). Debian also lacks the `row.combo` badge on Sound popups, because 48 uses `CcDeviceComboBox` in a plain row, not an `AdwComboRow` (certain from the `.ui`).

## Sidebar entries (this group)

| Item | mac reference | Arch 51 | Debian 48 | Gap | Cert | Fix |
|---|---|---|---|---|---|---|
| Notifications | red squircle, bell | `notifications` in `panel_order`, `.pulsar-icon-notifications` = `#ED5F5D` (`pulsar.css:163-166`, `cc-panel-list.c:383`) | same order (`cc-panel-list.c:400`), CSS shared | none on color; glyph is the GNOME bell-symbolic, not a filled bell | inferred (glyph) | none |
| Sound | red squircle, speaker with waves | `.pulsar-icon-sound` `#ED5F5D` | same | none on color | certain | none |
| Focus | purple squircle, moon | no entry | no entry | no GNOME panel | certain | hide (already hidden) |
| Screen Time | indigo squircle, hourglass | `wellbeing` row, `.pulsar-icon-wellbeing` `#9A57A3` (`pulsar.css:168-170`) | same | mac purple is bluer than `#9A57A3`; minor | inferred | CSS (one token) |

Group order: both builds put `notifications`, `sound`, `wellbeing` together, ended by a separator, matching the mac group minus Focus (`cc-panel-list.c:383-386` Arch, `:400-403` Debian). Certain.

## Page 16: Notifications

| # | Section | mac reference | Arch 51 | Debian 48 | Cert | Fix |
|---|---|---|---|---|---|---|
| N1 | Hub header | Card: red bell squircle, "Notifications", gray description, blue "Learn more..." | `CcHubHeader` via 0600, icon `org.gnome.Settings-notifications-symbolic`, color `#ED5F5D`, 40 px squircle (`pulsar.css:288-298`). Match | Same via `.ui` port (0600) and `cc-hub-header.ui`. Match | certain | none |
| N1b | Hub header copy | "...if they play a sound, and which apps can send them." | "...and which apps can send them." (no sound clause) | same string | certain | patch (string, both builds) |
| N2 | "Notification Center" heading and blurb | 21 px bold heading, 2-line gray text | Group title plus description from 0600; heading style `pulsar.css:211-223` | same patch, same CSS | certain | none |
| N2b | Blurb copy | "...in the top-right corner of your screen. You can show and hide ... by clicking the clock in the menu bar." | "...at the top of the screen." (GNOME Shell shows the clock in the center) | same | certain | patch (string); keep GNOME-accurate wording, owner call |
| N3 | "Show previews" popup (When Unlocked) | Card row with value text and round chevron badge | No such row; GNOME has no previews setting. Nearest key is `show-in-lock-screen` | same | certain (no row in patch; keys in schema) | none: do not add |
| N4 | "Show Notifications:" sub-rows (display sleeping, screen locked, mirroring) | Indented switch rows | Upstream group holds the DND switch (`dnd_row`) and, by the hunk's 14 context lines, one more row (lock-screen notifications). No GNOME key for display-sleeping or mirroring | same | inferred (lock row implied, not shown in the hunk) | none for the missing keys |
| N4b | Do Not Disturb switch | Not on this page (it lives in Focus) | `dnd_row` inside "Notification Center" | same | certain | none; it stands in for the Focus page |
| N5 | "Application Notifications" heading | Bold 21 px | Renamed from "App Notifications" by 0600 | Renamed by the `.ui` port | certain | none |
| N6 | App list card | Rows: rounded app icon, name, gray subtitle, trailing chevron, hairlines | Prefix icon (large), title, subtitle bound to `enable` (On/Off) by the 0600 `.c` hunk (`secondary-label` to `subtitle`); gray subtitle `css/notifications.css:10-12`; card radius and hairlines `pulsar.css:100-104,193-207` | Row structure is upstream 48. Debian 0600 has no `.c` hunk, so the On/Off value is not moved into a subtitle (the Arch hunk edits `g_settings_bind_with_mapping (..., "secondary-label", ...)`) and the subtitle CSS has nothing to match | certain that the Debian patch lacks the `.c` hunk; the 48 row type is inferred | Debian: CSS only (style the trailing value gray). Port the `.c` hunk only if the 48 source has the same call (check in the build) |
| N6b | App row subtitle content | Which alert types are on ("Badges, Sounds, Desktop") | On/Off only (`on_off_label_mapping_get`) | same | certain | patch (small, Arch first): build the subtitle from `show-banners`, `enable-sound-alerts`, `show-in-lock-screen` (all exist in the schema). Optional, low priority |
| N6c | App icon rounding | Rounded icon | `css/notifications.css:3-8` targets `image.lowres-icon` (32 px, 8 px radius). GTK adds `lowres-icon` only to some icons, so unflagged app icons are skipped | same rule | inferred | CSS (select the row prefix image instead) |
| N6d | Chevron | Light gray, right | Row is activatable with an arrow | same | inferred | none |
| N7 | Switches | Pill, blue on, gray off, light thumb | libadwaita default switch, accent when on; no Pulsar rule | same | inferred | none |

## Page 17: Sound

| # | Section | mac reference | Arch 51 | Debian 48 | Cert | Fix |
|---|---|---|---|---|---|---|
| S1 | "Sound Effects" group position | First group, heading "Sound Effects" | Moved to the top and renamed by 0400. Rows: Volume Levels, Alert Sound, Startup Sound | Same intent, see S2 | certain | none (Arch) |
| S2 | Debian group structure after 0400 | n/a | Clean: patch dry-run applies to the overlay `.blp` | Applying `patches-gnome48/0400` to the overlay `.ui` gives valid XML (`xmllint`) but wrong nesting: the "Sound Effects" group is never closed, so the Output, Input and "no devices" groups become children of it. Volume Levels and Alert Sound trail the group and land in its list | certain (patch applied to the overlay file in a scratch copy) | patch (rewrite Debian 0400: close the group, then add the two rows) |
| S2b | Effects row order | Alert sound first | Volume Levels, Alert Sound, Startup Sound | Startup Sound first, then Volume Levels, Alert Sound (add order in the nested group) | certain | patch (with S2) |
| S3 | Alert sound row | Inline popup ("Boop", round badge) plus play button | `CcListRow` with arrow, opens a sub page (`alert_sound_activated_cb`); no popup, no play button | same | certain | overlay (popup row plus play action in C). Large; likely leave as is |
| S4 | "Play sound effects through" popup | Popup row | none in GNOME | none | certain | hide (no setting) |
| S5 | Alert volume slider | Slider with 6 tick dots and speaker end icons | Alert volume is on the Volume Levels sub page, not here | same | certain | none |
| S6 | Effect toggles (startup, UI sounds, volume feedback) | 3 switch rows | Startup Sound switch only. `event-sounds` and `input-feedback-sounds` exist in `org.gnome.desktop.sound` but have no row in this panel | same | certain | none: adding rows adds settings the panel does not show (owner decision) |
| S7 | "Output & Input" structure | One group: Output / Input segmented control plus a Name / Type device table | Separate "Output" and "Input" groups with header-suffix level bars, device combo, Configuration combo, sliders | same layout | certain | overlay (segmented control plus list in `cc-sound-panel.{blp,c}`). Large; own ticket if wanted |
| S7b | Device picker control | Table row with highlighted selection | `CcDeviceComboRow` (`AdwComboRow`) gets the shared round-chevron badge (`pulsar.css:272-280`) and gray value (`css/sound.css:28-30`) | `CcDeviceComboBox` and `CcProfileComboBox` inside an `AdwPreferencesRow` plus `GtkBox` (`cc-sound-panel.ui:48-60`), not a `row.combo`. Both selectors are inert, so the popup is a stock dropdown | certain (selectors vs `.ui`); the 48 widget class is inferred | CSS (Debian only: restyle the dropdown button in those rows with the same badge) |
| S8 | Output volume slider and Mute | Slider with speaker end icons and a "Mute" checkbox below | `CcVolumeSlider`: flat speaker button at the start doubles as mute, styled gray (`css/sound.css:8-20`). No right-hand loud icon, no "Mute" label. Tick marks only if the widget adds them | same slider widget | inferred | patch (marks plus a loud-speaker end image in the volume slider, shared with Debian) |
| S9 | Slider look | Blue fill, white 24 px thumb | `pulsar.css:234-263` | same CSS | certain | none |
| S10 | Balance slider | "Left" and "Right" labels under the ends | `CcBalanceSlider`; mark labels styled by `pulsar.css:265-268` | same | inferred | none, or patch if the widget has no end marks |
| S11 | Fade, Subwoofer, Test..., level bar | Not on mac | Shown when the device exposes them | same | certain | none (GNOME-only, keep) |
| S12 | Input group | Same table, Input tab | Input group: device combo, Configuration, Input Volume | same | certain | follows S7 |
| S13 | Help "?" button | Round `?` bottom right | none | none | certain | hide (no equivalent) |

## Page 18: Focus

| # | Section | mac reference | Arch 51 | Debian 48 | Cert | Fix |
|---|---|---|---|---|---|---|
| F1 | whole page (Do Not Disturb row, Add Focus..., Share across devices, Focus status) | 4 cards | No panel id in `panel_order` (`cc-panel-list.c:380-386`); DND exists only as `dnd_row` in Notifications | same (`cc-panel-list.c:398-403`) | certain | hide; nothing to build |

## Page 19: Screen Time

The GNOME `wellbeing` structure below comes from the 1400 hunks and `css/screen-time.css`; row types beyond the hunks are inferred from upstream memory.

| # | Section | mac reference | Arch 51 | Debian 48 | Cert | Fix |
|---|---|---|---|---|---|---|
| T1 | Hub header | Not present (page opens on "Activity") | Added by 1400: purple (`#9A57A3`) hourglass header with description and "Learn more..." | same via `.ui` port | certain | none |
| T2 | "Activity" (App & Website Activity, Notifications, Pickups) | 3 link rows with colored icons and chevrons | Group renamed "Usage" by 1400, holds a statistics row (`CcScreenTimeStatisticsRow`) and an info menu in the header suffix; no link rows | same | certain (patch) | none: no GNOME equivalents. Optional: rename "Usage" to "Activity" (string patch, both builds) |
| T3 | "Limit Usage" (Downtime, App Limits, Always Allowed, Screen Distance) | 4 link rows with icons | "Screen Limit" group (daily limit and grayscale rows) | same | inferred | none (meanings differ). Optional: rename the group (string patch) |
| T4 | "Communication" and "Restrictions" | 2 + 1 link rows | none | none | certain | hide (no setting) |
| T5 | Break reminders | not on mac | "Break Reminders" group with break schedule rows (`CcBreakScheduleRow`) | same | certain (class named in the patch) | none |
| T6 | Row subtitles | gray | gray via `css/screen-time.css:3-5` | same CSS | certain | none |
| T7 | Prefix icons on rows | colored squircles | none | none | inferred | patch (prefix images with squircle classes). Large for little gain; skip unless the owner wants it |
| T8 | "Share across devices" and "Lock Screen Time Settings" toggles | two switch cards | none | none | certain | hide (no setting) |
| T9 | Card, heading, hairline metrics | 12 px cards, 21 px bold headings | shared `pulsar.css` | same | certain | none |

## Cross-cutting findings

1. Debian already consumes `pulsar.css` and all `css/*.css` (`prepare-assets.sh:244-272`). A Debian gap marked CSS is a rule that targets an Arch-only widget, not a missing file.
2. The one structural defect is Debian patch 0400 (S2). Fix it before Sound CSS work, since the nested group changes heading margins (`pulsar.css:211-218` uses `preferencesgroup:first-child`).
3. Settings GNOME lacks (previews popup, display-sleeping and mirroring rows, "Play sound effects through", Focus page, Communication, Restrictions, Share across devices) are marked none or hide, per the map note: restyle only panels GNOME has.
4. Possible ticket slices for the map owner:
   - a. Debian 0400 rewrite.
   - b. Sound slider marks and loud icon (shared patch).
   - c. Debian Sound dropdown badge (CSS).
   - d. Notifications app-icon selector fix (CSS) and Debian subtitle styling.
   - e. Optional strings: hub header copy, Notification Center blurb, "Usage" and "Screen Limit" renames.
   - f. Optional, large: segmented Output/Input table (overlay).

## Not verified

- Upstream 48 and 51 `cc-notifications-panel`, `cc-wellbeing-panel`, `cc-volume-slider` and `cc-balance-slider` were not read. Everything marked inferred depends on them.
- No build was run. GTK node names (`lowres-icon`, dropdown nodes on 48) are untested.
- Spanish strings for any renamed label belong in `overlay/po/pulsar-es.po` (existing entries not checked).
