# Control Center gap matrix: Connectivity group (Wi-Fi, Bluetooth, Network, VPN, Battery)

Issue: #263 (map #259). Strategy from #262: Arch leads, Debian hand-ports to `.ui`; Debian keeps the upstream 48 layout where widget trees differ.

Evidence is code only. Reference: `~/Downloads/setting-app/02..06-*.png` (dark, macOS 26). Compared against `arch/pkgbuilds/gnome-control-center/` (`overlay/`, `overlay/css/*.css`, `overlay/pulsar.css`, `patches/`) and `pulsaros-control-center/` (`overlay-gnome48/`, `patches-gnome48/`).

Limits of this note:
- No upstream gnome-control-center 48 or 51 tree is checked out in the repo. Upstream widget structure (what a panel contains before our patches) is therefore recalled, not read. Every claim that depends on it is marked **inferred**. Claims read directly from repo files are **certain**.
- `BluetoothSettingsWidget` is libgnome-bluetooth, not in this repo. Its tree is **inferred**.
- Screenshots hold real names (networks, devices); nothing from them is copied here beyond layout.

Fix kinds: **CSS** = `overlay/css/*.css` or `pulsar.css` (Debian gets it free, `prepare-assets.sh:244-264`). **Patch** = new numbered patch (Arch `.blp`, Debian `.ui` twin). **Overlay** = whole-file C or UI replacement (Arch `overlay/`, Debian `overlay-gnome48/`, which differ). **Skip** = no GNOME equivalent or a setting GNOME lacks; leave as is. **Hide** = no GNOME panel.

## 1. Sidebar rows and order

Reference order (one group, then a gap before General): Wi-Fi, Bluetooth, Network, VPN, Battery. Selected row is a solid blue pill; tiles are glossy gradient squircles with a white glyph.

Source: `panel_order[]` in `overlay/shell/cc-panel-list.c:360-367` (Arch) and `overlay-gnome48/shell/cc-panel-list.c:377-384` (Debian), identical in this group: `wifi, bluetooth, network, wwan, mobile-broadband, power, separator`. Colors: `pulsar.css:127-143`.

| # | Item | Reference | Arch 51 | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| S1 | Order of the five rows | Wi-Fi, Bluetooth, Network, VPN, Battery | wifi, bluetooth, network, (wwan, mobile-broadband), power: same order minus VPN | Same list | certain | none |
| S2 | VPN row | Own sidebar row and page | No VPN panel. VPN is a group inside the `network` panel (`cc-network-panel.blp`, "VPN" group, `box_vpn`) | Same (upstream 48 network panel) | certain (Arch), inferred (48) | **Hide**: add no row. VPN is restyled inside Network (N, V). An alias row needs `cc-panel-list.c`/`cc-window.c` overlay edits and invents a page, so not recommended |
| S3 | wwan, mobile-broadband rows | Absent | Listed in `panel_order`; upstream shows them only with a modem. Same blue as Wi-Fi (`pulsar.css:130-131`) | Same | inferred | none |
| S4 | Group gap before General | Larger gap, no divider | `separator` then 18 px `.pulsar-group-gap` via `header_func` (`cc-panel-list.c:488-501`) | Same file ported | certain | none |
| S5 | Tile colors | Wi-Fi, Bluetooth, Network, VPN blue; Battery green | wifi, bluetooth, network flat `#0088FF`; power flat `#79B757` (`pulsar.css:127-143`) | Same CSS | certain | CSS only if the glossy gradient is wanted (per-id gradient on `.pulsar-icon-*`) |
| S6 | Tile glyphs | Distinct glyphs (wifi fan, bluetooth rune, globe, battery bar) | White symbolic icon from each panel's icon name at 16 px in a 24 px tile (`cc-panel-list.c:245-256`). Glyphs are GNOME's, so Network is not a globe | Same | certain (mechanism), inferred (exact glyph per panel) | Overlay: map ids to icons from `arch/.../icons/` (239 files) in `cc-panel-list.c`. Debian has no `icons/` (`prepare-assets.sh:440-445`), so it needs its own icon set first |
| S7 | Tile size | About 20 pt at 2x scale (row 32 pt) | 24 px tile, 32 px row (`cc-panel-list.c:829`) | Same | inferred (screenshot scale assumed 2x) | CSS, optional, low priority |

## 2. Wi-Fi (02)

Reference sections: (a) hub card: blue squircle icon, title, gray description with blue "Learn More…", master toggle on the right, a hairline, then the connected network row with green "Connected" dot, lock, signal, "Details…" button; (b) "Known Networks" heading + card (check mark on the active one, lock, signal, round "..." button); (c) "Other Networks" heading with a spinner + card of visible networks, same row layout.

Arch source: patch 1100 (hub header group, then `Stack device_stack`); `wifi.css`; shared metrics in `pulsar.css`. Debian: `patches-gnome48/1100` (1:1 `.ui`), same CSS.

| # | Section | Reference shows | Arch shows | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| W1 | Hub card: icon, title, desc, link | Squircle icon, "Wi-Fi", description, "Learn More…" | Matches: `CcHubHeader` with `network-wireless-symbolic`, `#0088FF`, description, "Learn more…" (patch 1100). Link case differs ("More" vs "more") | Same via `.ui` patch | certain | none (optional string tweak) |
| W2 | Hub card: master toggle | Toggle inside the card, right side | `CcHubHeader` has no switch (`cc-hub-header.blp`: icon, title, description, link only). The Wi-Fi switch stays where upstream puts it, the header bar (the shell adopts the panel's header bar, `cc-window.c:468-565`), beside the main menu | Same shape; upstream 48 switch location the same | certain (hub has no toggle), inferred (upstream switch in header bar) | Overlay + patch: add an optional switch to `CcHubHeader` bound to the panel's switch. `cc-hub-header.{c,h}` are byte-identical in both overlays, so one C change ports; only `.blp`/`.ui` and the panel patch differ |
| W3 | Hub card: connected network row | Row inside the same card under a hairline: name, green dot "Connected", lock, signal, "Details…" | Connected network is a normal row in the visible list (upstream marks it with an `active_label` suffix, kept by patch 1100). No green dot: `panel_set_status_dot` (patch 1200) is only used on ethernet and VPN rows. No "Details…" button; upstream has an options button per row | Same | inferred (upstream row contents), certain (no dot on wifi rows) | Patch: move the active row into the hub group and call `panel_set_status_dot(row,"on")`; relabel the option button "Details…". Dot CSS already exists (`network.css`) |
| W4 | Row suffix order | lock, signal, round "..." | Patch 1100 moves `encrypted_icon` (16 px) and `strength_icon` into suffixes: lock, signal, then the upstream `options_button` | Same | certain | none |
| W5 | Icon tint and margins in rows | Light gray lock, white signal | `wifi.css` selector `row > box.header > image` does not match suffix images: libadwaita puts suffixes in `box.header > box.suffixes` (the repo's own `network.css` uses `box.prefixes image`). The 0.85 alpha and 6 px margin look dead | Same CSS | inferred (libadwaita node tree) | CSS: retarget to `box.suffixes > image` |
| W6 | Round "..." button | 28 px circle with dots | `wifi.css` styles `button#options_button` as a 28 px circle. Works only if the builder id acts as a CSS name; unverified. Upstream icon is probably not dots | Same CSS | inferred | CSS: retarget by class; Patch: `view-more-symbolic` icon |
| W7 | "Known Networks" section | Heading + inline card of saved networks, check on active | Not inline. Upstream puts saved networks behind a "Saved Wi-Fi Networks" row that opens a subpage (`net-device-wifi` is not in the repo) | Same | inferred | Patch (large, own ticket per #262): inline the saved list as a group. Cheaper: keep the subpage and style the row |
| W8 | "Other Networks" heading and spinner | Heading, spinner at right | Upstream group is titled "Visible Networks" with a scan spinner. Heading size and weight come from shared CSS (21 px bold, `pulsar.css` section heading rules) | Same | inferred | Patch (string): "Visible Networks" to "Other Networks" |
| W9 | Card and row metrics | 12 px cards, about 45 px rows, inset hairlines | Shared `pulsar.css` rules apply to `list.boxed-list` in `.content-pane` | Same CSS | certain | none |
| W10 | Check mark on the active known network | Check | None | None | inferred | Skip, tied to W7 |
| W11 | Round "?" button bottom right | Round "?" | No equivalent on any page | Same | certain | Skip (no GNOME equivalent; global, not Wi-Fi only) |

## 3. Bluetooth (03)

Reference: hub card (icon, title, description, "Learn more…", toggle, hairline, "This Mac is discoverable as … while Bluetooth Settings is open"); "My Devices" heading + card (device photo, name, "Not Connected", (i) button); round "?"; "Nearby Devices" heading with spinner + card with centered "Searching…".

Arch: patch 1600 puts a clamped `CcHubHeader` above `BluetoothSettingsWidget`; `bluetooth.css`. Debian: `1600` in `.ui`, same CSS.

| # | Section | Reference shows | Arch shows | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| B1 | Hub card: icon, title, desc, link | As above | Matches (`bluetooth-active-symbolic`, `#0088FF`, patch 1600) | Same | certain | none |
| B2 | Hub card: master toggle | Toggle in the card | No switch in `CcHubHeader`. The upstream Bluetooth switch is in the header bar and stays there | Same | certain (hub), inferred (upstream) | Same `CcHubHeader` switch change as W2; the Bluetooth patch binds it to the existing switch |
| B3 | Discoverable text in hub card | Gray sentence in the card under a hairline | Upstream shows the "Visible as …" text inside `BluetoothSettingsWidget`, outside our card. The widget is in libgnome-bluetooth, so no patch here reaches it | Same (system lib; Trixie version may differ, not verified) | inferred | Overlay: read the adapter name in panel C and set it as an extra hub label. CSS cannot move a widget |
| B4 | "My Devices" and "Nearby Devices" headings | Bold 21 px | The widget titles its lists "My Devices" and "Nearby Devices". The heading CSS in `pulsar.css` only matches `preferencesgroup > box > box.header`, so it applies only if the widget uses `AdwPreferencesGroup` (unverified) | Same; Trixie widget may be older | inferred | CSS if groups, otherwise Skip |
| B5 | Device row height and gray status | Tall rows, gray "Not Connected" | `bluetooth.css`: `list.boxed-list > row.activatable` min 56 px and `label.dim-label` 0.6 alpha. The selector covers every boxed-list activatable row in `.content-pane`, so it also changes other panels | Same CSS, same leak | certain (selector scope) | CSS: add `styles ["pulsar-bluetooth"]` in patch 1600 and prefix the selectors |
| B6 | Per-row (i) info button | Circled "i" | Upstream row has an arrow or settings button; no restyle in `bluetooth.css` | Same | inferred | CSS: icon swap via `-gtk-icon-source`, as the combo badge in `pulsar.css` |
| B7 | Device photos | Product images | Symbolic device-type icons from the widget | Same | inferred | Skip (no GNOME source for product art) |
| B8 | "Searching…" placeholder | Centered gray text in a card | Upstream shows a spinner or placeholder row in the nearby list | Same | inferred | Skip, or CSS gray centered label |
| B9 | Round "?" button | Round | None | None | certain | Skip |

## 4. Network (04)

Reference: card 1: Wi-Fi row (blue tile, green-dot "Connected", chevron); card 2: "VPN & Filters" (blue tile, green-dot "Active", chevron) and "Firewall" (orange tile, gray-dot "Inactive", chevron); heading "Other Services"; card of devices (gray tile, name, red-dot "Not connected", chevron); bottom "..." split button and "?".

Arch: `overlay/panels/network/cc-network-panel.blp` (full overlay), `network.css`, patch 1200. Debian: no network overlay; upstream 48 `cc-network-panel.ui` plus patch 1200 in `.ui`.

| # | Section | Reference shows | Arch shows | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| N1 | Group order and first card | Wi-Fi status row first | First group is "FlyDrop" (Pulsar-only row "FlyDrop File Sharing" with "Settings…" button). No Wi-Fi row; Wi-Fi is a separate panel | No FlyDrop (no network overlay). Upstream 48 starts with the device groups | certain (Arch), inferred (48) | Overlay (Arch `.blp`/`.c`): move FlyDrop to the bottom or off this page and add a Wi-Fi row that opens the `wifi` panel. Debian: patch the 48 `.ui` for the same row only if cheap |
| N2 | Wi-Fi status row | Tile, dot "Connected", chevron | None | None | certain | Overlay (see N1). Subtitle needs NMClient state; `panel_device_status_to_localized_string` exists in `panel-common.c` |
| N3 | "VPN & Filters" and "Firewall" cards | Two chevron rows | VPN is a group (connection list, "+" header button). No Firewall row. The repo has a `pulsaros-firewall` package, but a Firewall row would add a setting to this page that GNOME lacks | No Firewall | certain | Overlay; owner decision. Recommend Skip Firewall, restyle the VPN group (V) |
| N4 | "Other Services" heading | Heading + card of devices | Ethernet devices live in `box_wired`, a vertical box of per-device `NetDeviceEthernet` groups with no group title. The heading would come from `title: _("Other Services")` on the group | Same upstream 48 widget | certain (Arch has no title), inferred (48) | Patch (Arch blp) add title; Debian patch the `.ui` group title |
| N5 | Device row content | Gray tile (32 px), device name, dot state, chevron | Patch 1200: prefix `network-wired-symbolic`, title hard-set to "Wired", subtitle = status, dot class (on, idle, off). `network.css`: prefix becomes a 32 px rounded tile, subtitle gets the colored dot. Title is "Wired" for every NIC. Row control is the upstream on/off switch, not a chevron | Same via `.ui` 1200 | certain | Patch: title = device description (`nm_device_get_description`). The chevron needs the row to open a page; otherwise Skip |
| N6 | Dot colors and states | Green connected, gray inactive, red not connected | `network.css`: on `#34c759`, off `#ff3b30`, idle `#8e8e93`. Patch 1200: activated gives on, off-switch states give idle, else off | Same | certain | none |
| N7 | Tile colors per row | Blue Wi-Fi and VPN, orange Firewall, gray devices | One rule: gray `#8e8e93`, blue `#0a84ff` when `.pulsar-status-on`. A connected ethernet tile turns blue; the reference keeps device tiles gray | Same CSS | certain | CSS: key tile color by a per-row class, not by state |
| N8 | Bluetooth (PAN) group | Absent | Group "Bluetooth" `box_bluetooth`, hidden unless a PAN device exists | Same upstream | certain | Skip (GNOME setting) |
| N9 | Proxy row | Absent | Group "Proxy" with an arrow `CcListRow` | Same | certain | Skip (GNOME setting) |
| N10 | "..." split button and "?" | Bottom right | None | None | certain | Skip |
| N11 | Card and row metrics | 12 px cards, inset hairlines | Shared CSS | Same | certain | none |

## 5. VPN (05): hide the row, restyle the VPN group in Network

Reference: card with shield tile, "VPN", red-dot "Disconnected", a toggle, an (i) button; then "About VPNs & Privacy…" on the left, a "+" split button and "?" on the right.

There is no GNOME VPN panel. The VPN group inside Network is the nearest content.

| # | Section | Reference shows | Arch shows (Network panel, VPN group) | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| V1 | Page and sidebar row | Own page | No panel | No panel | certain | **Hide** (S2) |
| V2 | VPN row | Tile, name, dot text, toggle, (i) | `NetVpn` row: prefix `network-vpn-symbolic` (patch 1200), subtitle "Connected"/"Not connected" with dot, `device_off_switch` suffix. Gray 32 px tile via `network.css`; reference tile is blue. Upstream also has an options suffix button | Same | certain (patch), inferred (options button) | CSS: blue tile for VPN rows (needs a `pulsar-vpn` class from patch 1200); (i) icon swap as B6 |
| V3 | Add button | "+" split button, bottom right | Flat `list-add-symbolic` button in the group header (`header-suffix`). Empty state "Not set up" | Upstream 48 has the same header "+" (inferred) | certain (Arch) | CSS: give the header button the `.pulsar-nav-capsule` rounded background; position stays |
| V4 | "About VPNs & Privacy…" | Left button | None | None | certain | Skip (macOS-specific) |

## 6. Battery (06)

Reference: header shows a two-line title ("Battery" and "Battery Level: 92%" with a glyph). Cards: "Battery Health: Normal (i)"; "Energy Mode" heading + gray help text + card with two popup rows ("On battery", "On power adapter", value "Automatic" with round chevron badge); usage card with a segmented "Last 24 Hours / Last 10 Days" control and two charts; bottom "Options…" and "?".

Arch: patch 1300 adds class `pulsar-power` to both stack pages; `battery.css`; Arch-only overlay `cc-power-panel.c` (adds 1/2/5/10 min delays only, line 663). Debian: `1300` in `.ui`, no power overlay.

| # | Section | Reference shows | Arch shows | Debian 48 | Certainty | Fix |
|---|---|---|---|---|---|---|
| P1 | Page header | Bold 28 px "Battery" with a gray subtitle line | The panel has two stack pages (`general_page`, `power_saving_page`, icons `org.gnome.Settings-power-symbolic`, `power-saving-symbolic`), so the header most likely holds a view switcher. `update_header()` adds the bold title only if the bar has no title widget (`cc-window.c:553-566`), so the switcher stays and no "Battery" title shows | Debian `cc-window.c` has the same rule (`overlay-gnome48/shell/cc-window.c:604`) | inferred (switcher is the title widget) | Patch: merge Power Saving into one page, or Overlay: a subtitle on the adopted title. Large, own ticket |
| P2 | Battery Health row | "Battery Health  Normal (i)" | Group "Battery Level" with `CcBatteryRow` (UPower level, `cc-power-panel.c:125-130`, `291-313`). Charging section with radios "Maximize Charge" / "Preserve Battery Health" when supported (`157-180`, `332`). No "Normal" status | 48 charging section presence not verified | certain (Arch), inferred (48) | Skip the "Normal" status (no GNOME source). Restyle only |
| P3 | "Energy Mode" heading and help text | Heading + 2 gray lines | Group "Power Mode" with an info paragraph. `battery.css` bolds the heading under `.pulsar-power` and makes wrapping action-row text 12 px gray | Same CSS | certain | none |
| P4 | Mode rows | Two popup rows (Automatic) | Radio rows (Balanced, Performance, Power Saver) with the check button on the left and a gray subtitle (`battery.css`). One profile only; power-profiles-daemon has no per-power-source setting | Same | certain | Skip: "On battery / On power adapter" is a setting GNOME lacks. Keep radios, CSS only |
| P5 | Popup chevron badge | Round gray up/down chevron | `pulsar.css` styles `row.combo ... image.dropdown-arrow` as a 36 px badge. `battery.css:30-33` grays the `row.combo` suffix label. Applies to the suspend delay rows only if they are combo rows | Same CSS | inferred | none |
| P6 | Usage history, tabs, charts | Segmented control, 2 charts | None; the power panel has no history | None | inferred | Skip (needs a new data source) |
| P7 | "Options…" button | Bottom right | "Show Battery Percentage" switch row and suspend/power button groups | Same | certain | Skip |
| P8 | Power Saving page | Not in reference | Second stack page (auto brightness, dim, blank screen, and more) with the `pulsar-power` class | Same | certain | none; goes away when P1 is resolved |
| P9 | Card and row metrics | 12 px cards, inset hairlines | Shared CSS | Same | certain | none |

## 7. Debian 48 notes

- CSS and the four panel patches in this group (1100, 1200, 1300, 1600) have 1:1 ports; every CSS-only fix above reaches Debian with no extra work.
- Debian differs on: no `cc-network-panel` overlay (no FlyDrop group, N1), no `cc-power-panel.c` overlay (no extra delay options, no visual effect), own `cc-window.c` (title adoption exists; `cc-window.ui` has no capsule, the C builds it).
- The libgnome-bluetooth widget and the upstream 48 Wi-Fi, Network and Power trees were not read. Recheck every inferred item against the 48 `.ui` when its Debian port ticket is written.
- `cc-hub-header.{c,h}` are byte-identical in both overlays (#260), so the toggle property (W2, B2) is one C change plus `.blp` (Arch) and `.ui` (Debian) twins.

## 8. Suggested ticket slicing (owner decision)

1. CSS only (Debian free): W5, W6, B5 scope fix, B6, V2, V3, N7, S5.
2. Hub header toggle (W2, B2): one C change plus two panel patches.
3. Network panel overlay (N1, N2, N4, N5 title): Arch overlay, Debian patch.
4. Wi-Fi inline known and other networks (W3, W7, W8): large, own ticket.
5. Battery header and page structure (P1): large, own ticket.
6. Hide VPN row (S2): decision only, no code.
