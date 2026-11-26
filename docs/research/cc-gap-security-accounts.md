# Control Center gap matrix: security and accounts

Issue: #266 (map #259). Group: profile row (01), Lock Screen (20), Privacy & Security (21), Touch ID & Password (22), Users & Groups (23), Internet Accounts (24).

Evidence is code only, no VM capture. Arch = `arch/pkgbuilds/gnome-control-center` (51.1, `.blp`). Debian = `pulsaros-control-center` (48, `.ui`). The upstream 48 and 51 trees are not in the repo, so claims about stock widget trees are inferred. Screenshots show real account data; none is copied here.

Strategy from #262: Arch leads; Debian ports CSS and shared patches as they are and keeps the upstream 48 layout where widget trees differ.

Legend: certainty = **certain** (read in repo files) or **inferred** (from stock GNOME behaviour or CSS reasoning). Fix = CSS, patch (small `.patch`), overlay (whole-file replacement).

## 1. Summary

- Shared metrics already match the references: 12 px card radius, 20 px card gap, ~38 px rows, inset hairlines, 21 px bold headings, 28 px page title, back/forward capsule, round up/down badge on combo rows (`overlay/pulsar.css:142-290`). Debian gets all of it (CSS appended by `prepare-assets.sh`).
- Biggest structural gap: macOS has five separate sidebar pages (Lock Screen, Privacy & Security, Touch ID & Password, Users & Groups, Internet Accounts). GNOME has three panels (`privacy`, `users`, `online-accounts`, `panel_order` in `overlay/shell/cc-panel-list.c:389-391`). Lock Screen is a sub-page of Privacy (`'screenlock'`), and Touch ID is a row that spawns an external app. A restyle cannot add pages; options are hide or accept the difference (see section 8).
- Privacy and Security: hub header and sections exist, but the macOS page is one flat list of per-permission rows with icon, subtitle and count; GNOME shows three titled groups.
- Users: row restyle (40 px avatar, role subtitle, round info button) exists in both builds through patch 1900. Rest of page (Add Group, auto-login subtitle, network account server) has no GNOME equivalent.
- Internet Accounts: nothing exists. No overlay, patch or CSS touches `online-accounts` except the sidebar squircle colour.

## 2. Profile row (01)

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| Sidebar profile row | 40 px avatar, bold name, grey "Apple Account" caption, rounded 10 px row; filled accent when the page is open | `cc-window.blp:55-100`: flat button, `Adw.Avatar` 40, `heading` name, `caption dim-label` second line, radius 10 (`pulsar.css:36-38`) | Same widget tree and classes in `cc-window.ui:54-95`; overlay C has same label | Layout matches | certain | none |
| Second line text | Account provider name | Hard-coded "Local Account" (`cc-window.c:922`) | Same (`cc-window.c:993`) | Text differs by design. No Apple account exists; keep as is | certain | none (decision, not gap) |
| Open-page state | Row turns solid blue with white text when its page is open | Only `border-radius: 10px`; no `:selected` or `.active` style. Clicking calls `set_active_panel_from_id("users")` (`cc-window.c:950-953`), so the Users list row highlights, not the profile button | Same | Profile row never shows the selected look | inferred (no code toggles a class on the button) | CSS plus small C change (add/remove `.pulsar-profile-active` class on panel change in `cc-window.c`; CSS reuses `--accent-bg-color`, white text). Debian needs the same C edit in its own `cc-window.c` |
| Avatar | Generic grey silhouette | Real photo from `.face`, `.face.icon`, AccountsService, else initials (`cc-window.c:927-947`) | Same logic | Initials vs silhouette when no photo | inferred | CSS (grey avatar colour) or accept |
| Page it opens | Apple Account page: large avatar, name, email, link cards (Personal Information, iCloud, Devices ...) | Opens `users` panel (user page, 120 px avatar, name entry, password row) | Opens stock 48 users panel | No GNOME equivalent of Apple Account. Closest is the user page | certain | overlay (restyle `cc-user-page`) only for the avatar header; the link cards are not buildable (rule: add no setting GNOME lacks) |

## 3. Lock Screen (20)

Arch: sub-page `CcScreenPage` (`overlay/panels/privacy/screen/cc-screen-page.blp`), reached from a row in Privacy. Debian: stock 48 `CcScreenPage` (referenced in `cc-privacy-panel.ui:139`, no overlay file).

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| Page placement | Own sidebar entry "Lock Screen" with black squircle and padlock | No sidebar entry; sub-page of Privacy under the title "Screen Lock" | Same, stock page | Navigation differs | certain | overlay (new panel entry) or hide; see section 8 |
| Page title | "Lock Screen" | "Screen Lock" (`cc-screen-page.blp:5`) | "Screen Lock" (inferred from stock) | Wording | certain (Arch), inferred (Debian) | patch (rename string; add Spanish in `pulsar-es.po`) |
| Timeout card | Rows: display off on battery, display off on AC, require password; each a label plus round up/down popup | Rows: Blank Screen Delay (`CcNumberRow`), Automatic Screen Lock (switch), Lock Delay (`CcNumberRow`), Lock Screen Notifications (switch), USB protection (switch, hidden) | Stock, same row set (inferred) | Different semantics: GNOME has one blank delay (not per power source) and a switch plus delay (not a single "require password after"). `CcNumberRow` is an `AdwComboRow` subclass, so it gets the round badge from `pulsar.css:272` | inferred (`CcNumberRow` base class from stock source, not in repo) | none for badge (CSS already applies). Row semantics: no fix, GNOME lacks per-source blank |
| Biometrics group | Not on this page | Extra group "Biometrics & Presence Detection" row spawning `pulsaros-biometrics-settings` (`cc-screen-page.blp:15-26`, `.c:55-58`) | Absent (stock page) | Debian lacks the row, Arch has it; the row has no macOS counterpart on this page | certain | overlay (Debian: add `cc-screen-page` overlay) or drop the Arch row; decision needed |
| Show password hints / message when locked | Switch rows; "Set..." grey button beside the second | Not present. Closest: "Lock Screen Notifications" | Not present | No GNOME setting for hints or lock message | certain | none (add no setting GNOME lacks) |
| "When Switching User" heading and radios | Heading plus "List of users / Name and password" radios and a switch for power buttons | Not present | Not present | No GNOME setting | certain | none |
| Privacy-screen group | None | "Screen Privacy" group with Restrict Viewing Angle (`cc-screen-page.blp:80-87`), visible only with hardware | Stock, same | Extra group, hardware-gated | inferred | none |
| Intro text | None | `PreferencesPage description` text above the first group | Stock, same | Extra grey paragraph at the top; reference starts directly with a card | certain | CSS (hide) or patch (remove description) |
| Footer | "Accessibility Options..." pill button and round "?" button | None | None | Footer buttons absent | certain | none for Accessibility link would need a new row (skip); "?" help button is stock window chrome, not present |
| Switch look | Blue track, white round knob; off state grey | `Adw.SwitchRow` default. No switch CSS in `pulsar.css` or `css/*.css` (grep found none) | Same | Default libadwaita switch; accent already blue via `--accent-bg-color` | inferred | CSS only if the knob or track size differs on VM review |
| Hairlines, radius, bold heading | As in reference | Via shared CSS | Via shared CSS | Match | certain | none |

## 4. Privacy & Security (21)

Arch: `overlay/panels/privacy/cc-privacy-panel.blp` plus patch 0110 (hub header). Debian: `overlay-gnome48/panels/privacy/cc-privacy-panel.ui` plus patch 0110 (same header).

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| Hub header | Card: blue squircle with hand icon, bold "Privacy", grey two-line text, blue "Learn more..." | `CcHubHeader` with `icon-color #1c1c1e` (black), title "Privacy & Security", description, "Learn more…" link (patch 0110) | Same, same colour (patch 0110 port) | Squircle is black, reference is blue; title text differs ("Privacy & Security" vs "Privacy") | certain | patch (change `icon-color` to `#0088FF` in 0110 for both builds). Sidebar icon `.pulsar-icon-privacy` is `#1c1c1e` too (`pulsar.css:157-161`); reference sidebar icon for this page is blue, so CSS change there. Title: macOS says "Privacy"; leave, patch string if wanted |
| Location row | Separate card with blue arrow icon, label, count (4), chevron | Row "Location" with subtitle, `visible: false` until the page decides to show it | Same | Reference has its own card with a count suffix; ours sits in the "System" group, no count | certain | patch (move into own group, add count label suffix in C) |
| Permission list (Calendars, Contacts, Files, Full Disk Access, Home, Media, Passkeys, Photos, Reminders) | One card of 9 rows, coloured app icon, label, grey status subtitle, chevron | No such rows. GNOME has no per-app data permissions except Camera and Location | none | No equivalent settings | certain | none (add no setting GNOME lacks) |
| Second list (Accessibility, App Management, Automation, Bluetooth, Camera, ...) | One card with a count and chevron per row | Group "Devices": Cameras, Thunderbolt (hidden), Device Security. Group "System": Screen Lock, File History & Trash, Diagnostics | Same rows, same groups | Rows exist for 6 of the items only; ours use three titled groups ("System", "Biometrics & Presence", "Devices") where the reference has untitled cards. Titles render as 21 px bold headings (`pulsar.css:221-233`) | certain | patch (drop `title:` on the groups, or keep; low priority) |
| Row icons | 28 px coloured squircle with app glyph | `icon-name` points to stock symbolic icons (`org.gnome.Settings-*-symbolic`). No squircle CSS for row prefixes; `.pulsar-squircle` is used only in the sidebar | Same | Row icons are small monochrome glyphs, reference uses colourful squircles | certain (no CSS rule for row prefix icons) | CSS (style `row > box.header > image.icon` with radius and background) plus patch (per-row colour class). Same code both builds |
| Row subtitle | Grey status ("None", "10 apps") | Static descriptive subtitles | Same | Reference subtitles are state; ours are help text | certain | patch (small C) or accept |
| Biometrics row | Not on this page (separate Touch ID page) | Group "Biometrics & Presence" with one row, `system-users-symbolic` icon, spawns `pulsaros-biometrics-settings` | Same row, in `.ui` | Row has no counterpart here | certain | overlay (move the row to the Users page only) or keep |
| Chevron | Dim grey, thin | Stock `show-arrow` arrow | Same | Colour/weight unverified | inferred | CSS if needed |
| FileVault, Lockdown Mode, Security | Rows further down (not captured; screenshot is cut off) | Not present | Not present | No equivalent | inferred (screenshot ends at Camera) | none |

## 5. Touch ID & Password (22)

No GNOME panel. The closest are the Password row and the "Touch ID & Face ID" row in the user page, which spawns `pulsaros-biometrics-settings` (`cc-user-page.blp:93-104`, `cc-user-page.c:369-371`). Debian has no `cc-user-page` overlay; the stock 48 users page has a Password row only (inferred). Sidebar: Arch has no "Touch ID & Password" entry (`panel_order`).

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| Sidebar entry | "Touch ID & Password" with a fingerprint squircle | None. `icons/fingerprint.svg` exists in the Arch icon set but no sidebar id uses it | None | No page | certain | hide (no panel) or overlay (new thin panel that launches the external app) |
| Password card | Single row "A login password has been set", grey "Change..." button | `CcListRow` "Password" with arrow, under the Name entry (`cc-user-page.blp:70-80`) | Stock row (inferred) | Row has an arrow, not a "Change..." pill button; the sentence is not shown | certain (Arch), inferred (Debian) | patch (swap arrow for a suffix button; CSS for a grey rounded button) |
| Touch ID heading and text | Bold "Touch ID", grey paragraph with blue link | None | None | No equivalent text | certain | overlay only if the page is built; otherwise none |
| Fingerprint tiles ("Finger 1", "Add Fingerprint") | Centred glyph tiles | None in this repo (handled by an external app) | None | No in-panel fingerprint UI | certain | none (add no setting GNOME lacks) |
| Toggle list (unlock, Apple Pay, purchases, autofill, fast user switching) | One card with 5 switch rows | None | None | No GNOME settings for these | certain | none |
| Help button | Round "?" bottom right | None | None | Not present | certain | none |

## 6. Users & Groups (23)

Arch: `overlay/panels/system/users/cc-user-page.{blp,c}` plus patch 1900 and `css/users.css`. Debian: stock 48 users page plus patch 1900 port, plus `css/users.css` appended.

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| User list card | 3 rows: avatar, name, role subtitle, round info button at the right, hairlines | `create_user_row` (patch 1900): `pulsar-user-row`, 64 px, 40 px avatar, "Administrator" or "Standard" subtitle, flat circular info button; CSS in `users.css` | Same patch, same CSS | Matches. Subtitle says "Administrator" vs "Admin" | certain | patch string if wanted |
| Guest User row | Row "Guest User / Off" | Not present | Not present | No guest account in GNOME panel | certain | none |
| Add Group / Add User buttons | Two grey pills below the card, right-aligned | Arch stock add-user control is an `Add User…` button in the list page (`cc-users-page`); not changed by overlay | Same | Button style and alignment are default libadwaita (flat or pill, inferred); there is no Add Group | inferred | CSS (grey rounded button, right alignment); Add Group: none |
| Auto-login card | "Automatically log in as" popup (round up/down badge) with a grey explanatory subtitle; second row "Network account server" with "Edit..." button | Auto-login is a `Switch` in the per-user page (`cc-user-page.blp:106-120`), not a popup; info button for the explanation | Stock | Control type differs (switch vs popup). No network account server | certain | none for the switch type (a combo would add behaviour); "Network account server": none |
| Page header region | List only, no avatar header | List page is stock, matching | Same | Match | inferred | none |
| Per-user page (not in reference; opens from an info button) | Not captured | Avatar 120 px, name entry, rows, "Remove User…" destructive row (`cc-user-page.blp:30-208`) | Stock 48 layout | Not covered by screenshots | certain | none (outside this group; belongs to the not-yet-specified sub-pages) |
| Help button | Round "?" | None | None | Not present | certain | none |
| Heading and card metrics | As the reference | Shared CSS | Shared CSS | Match | certain | none |

## 7. Internet Accounts (24)

GNOME panel id `online-accounts`. Nothing in Arch overlay, patches or `css/` touches it; Debian is the same. The only styling is the sidebar squircle: blue (`pulsar.css:136-137`, shared with `users`).

| Section | Reference shows | Arch shows | Debian | Gap | Certainty | Fix |
|---|---|---|---|---|---|---|
| Account list card | Row: coloured icon, bold provider name, grey service list, chevron | Stock `CcOnlineAccountsPanel`: group of connected accounts (provider icon, name), plus a group of providers to add (inferred; source not in repo) | Stock 48 (inferred) | Shared metrics apply (card radius, hairlines, heading). Provider icons are stock, not squircles; subtitles may be default colour (shared `label.subtitle` rule applies) | inferred | CSS only if VM shows a drift |
| Add Account | Grey "Add Account..." pill plus round "?" | Stock "Add an Account" group of provider rows (inferred) | Stock | Reference is a single button; GNOME lists all providers inline | inferred | patch (large) or accept; no setting added |
| Page header | Title "Internet Accounts" | Title from stock `.desktop` data ("Online Accounts") | Same | Wording | inferred | patch string |
| Sidebar icon | Blue squircle with cloud | Blue squircle with stock `preferences-online-accounts` glyph (`icons/preferences-online-accounts.svg` in the Arch icon set) | Debian ships no `icons/` dir (copy step skipped per #260) | Debian has no per-panel glyph overrides; Arch has | certain | overlay (Debian: add icons), already tracked by the icon work in the map |

## 8. Pages with no GNOME panel

| macOS page | GNOME mapping | Recommendation |
|---|---|---|
| Lock Screen | Sub-page of `privacy` | Keep as sub-page. A separate sidebar entry needs a `panel_order` entry and a new panel class; not a restyle (overlay, medium) |
| Touch ID & Password | None (external app `pulsaros-biometrics-settings`) | Hide. Keep the existing rows that launch the external app |
| Apple Account (profile) | `users` | Keep as the profile-row target |
| Game Center, iCloud, Wallet (already in map) | None | Hide, per map |

## 9. Fix list by kind

CSS (shared, both builds):
- Row prefix icons as coloured squircles (privacy rows).
- Sidebar squircle for `privacy` from black to blue; check `users` and `online-accounts` colours against the reference.
- Grey pill style for suffix buttons ("Change...", "Add User...", "Add Account...").
- Profile row selected state.
- Hide the page `description` paragraph on the screen page (or patch).
- Switch knob and track, only if the VM shows a mismatch.

Patch (Arch first, Debian port second):
- 0110: hub header `icon-color` blue.
- Privacy: move Location to its own group with a count; drop group titles if wanted.
- Password row: replace the arrow with a "Change..." button.
- String renames (Lock Screen, Internet Accounts, Admin); add to `pulsar-es.po`.

Overlay:
- `cc-window.c`: toggle a class on the profile button when the `users` panel is active (Arch and Debian C files differ, so two edits).
- Debian: add a `cc-screen-page` overlay if the Arch biometrics row should exist there, or remove the row from Arch.
- Debian: `icons/` set (shared with other groups).

None (no GNOME setting, add nothing): per-app privacy rows, Guest User, Add Group, network account server, hints and lock message, switch-user radios, Touch ID toggles, fingerprint tiles, FileVault and Lockdown rows.

## 10. Debian notes

- CSS, hub-header patch 0110 and users patch 1900 apply with the same result as Arch; the Debian cell in each row above says "same" where the `.ui` twin carries the same widgets and classes.
- Where Debian lacks the Arch overlay (`cc-screen-page`, `cc-user-page`, network and power panels), Debian keeps the stock 48 layout; gaps there are CSS only unless a row says patch or overlay.
- The Trixie libadwaita version is not checked for the `Adw.ButtonRow` used in the Arch `cc-user-page.blp` (`remove_user_button`); an untested risk if a port reuses that file (carried over from #260).

## Not verified

- Stock upstream widget trees for `CcScreenPage` 48, `CcUsersPage` 48, `CcOnlineAccountsPanel` (all versions): upstream is not in the repo.
- No render. Colour, spacing and switch appearance are reasoned from CSS only.
- The portion of Privacy & Security below Camera, and any FileVault, Lockdown Mode rows, are outside the screenshot.
