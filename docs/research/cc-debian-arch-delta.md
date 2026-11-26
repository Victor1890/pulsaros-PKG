# Control Center: Debian 48 vs Arch 51.1 source delta

Issue: #260 (map #259). Read-only comparison of `pulsaros-control-center/` (Debian, gnome-control-center 48) and `arch/pkgbuilds/gnome-control-center/` (Arch, 51.1, `PKGBUILD:6`). Sources are the repo files cited below. Upstream 48 and 51 trees were not cloned, so upstream structure claims are inferred from what our patches and overlay touch.

## Answer in brief

Debian is already close to Arch on CSS and patches. It consumes the Arch CSS and has a 1:1 port of every Arch panel patch. The real delta is the overlay (full-file replacements of C and UI files) and the `.ui` versus `.blp` format. Arch `.blp` output cannot simply replace Debian `.ui` files, because the Arch files are written against 51 widget APIs and C code.

## 1. What prepare-assets.sh consumes from Arch

`pulsaros-control-center/prepare-assets.sh`:

| Arch asset | Consumed by Debian? | Ref |
|---|---|---|
| `overlay/pulsar.css` | Yes. Appended to `shell/style.css`; the `@media (prefers-color-scheme: dark)` block is moved to `style-dark.css` because GTK 4.18 drops it | lines 244-264 |
| `overlay/css/*.css` (15 files) | Yes, all, appended | lines 261-263 |
| `overlay/po/pulsar-es.po` | Via the Debian copy `overlay-gnome48/po/pulsar-es.po`, byte-identical | lines 290-295 |
| `overlay/shell/cc-hub-header.{c,h}` | Debian copies, byte-identical (a `.ui` replaces the `.blp`) | overlay-gnome48/shell |
| `patches/*.patch` (19) | No. Debian uses its own `patches-gnome48/` (section 2) | lines 266-272 |
| `overlay/**` (whole tree) | No for 48. Only used when `GNOME_CC_VER >= 50` | lines 218-231 |
| `pulsar-macos-style.patch` | No for 48. Only the 50+ fallback when the overlay dir is missing | lines 219, 228-230 |
| `icons/` | No. Debian reads `overlay-gnome48/icons`, which does not exist in the tree, so the copy is skipped | lines 440-445 |

Missing on the Debian side:
- Arch `0100-shell-register-hub-header.patch` is replaced by two `sed` lines (lines 245-247, gresource and `meson.build`).
- Debian has no `icons` of its own and no `.blp` shell files.
- The PKGBUILD applies overlay, then CSS, then patches (`PKGBUILD:115-133`). Debian applies the same order for 48, with its own overlay.

## 2. Per-panel table (patches)

All 19 Arch patches have a Debian port, except 0100 (done by `sed`). Debian adds 0050. The Debian ports edit `.ui`, the Arch ones edit `.blp`.

| Panel | Arch patch | Debian patch | Status |
|---|---|---|---|
| shell registration | 0100 | none (sed in script) | both, different mechanism |
| shell style provider | none | 0050 | Debian only |
| privacy | 0110 | 0110 | both |
| universal-access typing | 0200 | 0200 | both |
| system | 0300 | 0300 | both |
| sound | 0400 | 0400 | both |
| universal-access | 0500 | 0500 | both |
| notifications | 0600 | 0600 | both |
| search | 0700 | 0700 | both |
| keyboard | 0800 | 0800 | both |
| multitasking | 0900 | 0900 | both |
| wifi | 1100 | 1100 | both |
| network status dot | 1200 | 1200 | both |
| power | 1300 | 1300 | both |
| screen time (wellbeing) | 1400 | 1400 | both |
| mouse | 1500 | 1500 | both |
| bluetooth | 1600 | 1600 | both |
| display | 1700 | 1700 | both |
| printers | 1800 | 1800 | both |
| users | 1900 (`cc-users-page.c`) | 1900 (`cc-users-page.c`) | both |

## 3. Per-file table (overlay)

Debian `overlay-gnome48/` vs Arch `overlay/`. Line counts are Debian / Arch.

| File | State |
|---|---|
| `po/pulsar-es.po` | identical |
| `shell/cc-hub-header.c`, `.h` | identical |
| `shell/cc-hub-header` UI | Debian `.ui` only; Arch `.blp` only |
| `shell/cc-window.c` | both, differ (1180 / 1074) |
| `shell/cc-window` UI | Debian `.ui`; Arch `.blp` |
| `shell/cc-panel-list.c` | both, differ (1121 / 1005) |
| `shell/cc-object-storage.c` | Debian only (449 lines) |
| `panels/background/cc-background-panel.{blp,c,ui}` | both, differ (Debian carries both `.blp` and `.ui`) |
| `panels/keyboard`, `mouse`, `privacy`, `sound` `.c` | both, differ |
| `panels/keyboard`, `mouse`, `privacy`, `sound` UI | Debian `.ui`; Arch `.blp` |
| `panels/sound/cc-sound-panel.h` | both, differ |
| `panels/network/cc-network-panel.{blp,c,h}` | Arch only |
| `panels/power/cc-power-panel.c` | Arch only |
| `panels/privacy/screen/cc-screen-page.{blp,c}` | Arch only |
| `panels/system/users/cc-user-page.{blp,c}` | Arch only |
| `css/*.css`, `pulsar.css` | Arch only (Debian reads them from Arch) |

## 4. Blockers for a straight 48 to 51 port

- Format: Arch overlay and patches target `.blp` (Blueprint). The 48 tree builds from `.ui`. Debian therefore keeps hand-written `.ui` twins of every Arch `.blp` it uses.
- Libadwaita: Debian depends on the system `libadwaita-1-0` (`DEBIAN/control:8`) with no pinned version. The 51 `.blp` files use `using Adw 1;` with `Adw.BreakpointBin`, `Adw.Breakpoint` and `Adw.NavigationSplitView` (`overlay/shell/cc-window.blp:1-17`, `overlay/panels/background/cc-background-panel.blp:1-5`). Whether Trixie libadwaita provides every widget used was not tested. The Debian `cc-window.ui` already uses `AdwNavigationSplitView` and `AdwToolbarView`.
- Dark CSS: GTK 4.18 on Trixie ignores `@media (prefers-color-scheme)`, so the script rewrites the CSS (lines 248-260). This is a build-time fix, not a source delta.
- Panel moves: Arch has `panels/system/users/cc-user-page.c` and `panels/privacy/screen/cc-screen-page.c` as full overlays. Debian only patches `cc-users-page.c` (patch 1900) and has no screen page overlay. Whether 48 has these files at the same paths was not verified.
- Divergent C: `cc-window.c`, `cc-panel-list.c`, `cc-sound-panel.c` differ by 70 to 116 lines between the two overlays, so the C is not shared.

## 5. Can `blueprint-compiler` output of Arch `.blp` replace Debian `.ui`?

No, not as a drop-in.
- The script already tries it: it compiles every `.blp` in the tree to `.ui` (lines 279-288), but with `2>/dev/null || true`, so compile failures are silent.
- The Arch `.blp` bind to Arch C files (`cc-window.c`, `cc-panel-list.c`, ...), which differ from the Debian C. A compiled Arch UI could reference template children and callbacks the Debian C does not define.
- For `background`, Debian ships both `.blp` and `.ui`; the compile step overwrites the `.ui` with the `.blp` output, which can hide drift between them.
- Possible path: port the Debian C to match Arch and compile Arch `.blp`, but this needs the libadwaita check above first. Not attempted here.

## Not verified

- Upstream 48 and 51 trees were not read; panel structure claims come from the overlays and patches.
- No build was run, so `blueprint-compiler` behavior on Trixie is untested.
