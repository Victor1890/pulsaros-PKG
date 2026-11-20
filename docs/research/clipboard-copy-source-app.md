# Can a copy's source app be known on GNOME Wayland?

Ticket #182 (child of map #179). Evidence only, no decision.
Target: GNOME 48 and 51, Wayland. Mutter source read at tag/HEAD `51.1` (commit `9bc8cd84`, https://gitlab.gnome.org/GNOME/mutter). Extension sources read from default-branch HEAD.

## Short answers

| Approach | Can it name the source app? | Reliability |
|---|---|---|
| 1. GTK4 / GDK clipboard API (Launcher side) | No | n/a, no API |
| 2. Mutter `Meta.Selection` / `Meta.SelectionSource` (extension side) | No, not directly | Signal fires, but the source object carries no client, PID or window |
| 3. Focus window at `owner-changed` (extension side) | Yes, as a heuristic | Right for normal user copies, wrong or absent in several cases (below) |
| 4. Existing extensions | Clipboard Indicator and Pano use approach 3. GPaste has no app exclusion | Same limits as 3 |

Only approach 3 exists in practice. It is a heuristic, not an identity.

## 1. GTK4 / GDK clipboard

`GdkClipboard` has properties `content`, `display`, `formats`, `local`; one signal `changed`; no owner method.
- `changed`: "Emitted when the clipboard changes ownership."
- `local`: "TRUE if the contents of the clipboard are owned by this process."
- The page lists no API identifying another client or application as owner. `is_local()` only answers "is it us".
- Source: https://docs.gtk.org/gdk4/class.Clipboard.html

Why this is structural on Wayland: `wl_data_offer` / `wl_data_device.selection` carry only a mime list and a read fd. The protocol exposes no client identity to other clients (https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_data_device). GDK's Wayland backend therefore has nothing to surface.

Verdict: No. Launcher-only detection is impossible; the compositor-side extension is the only vantage point.

## 2. Mutter `Meta.Selection` and `Meta.SelectionSource`

Public API (Mutter `src/meta/meta-selection.h`, `src/meta/meta-selection-source.h`):
- `MetaSelection` signal `owner-changed(selection_type: uint, source: MetaSelectionSource)`. Emitted by `meta_selection_set_owner` and, with `source = NULL`, by `meta_selection_unset_owner` (`src/core/meta-selection.c`, lines ~79-87, 132, 156). Reached from JS via `global.display.get_selection()`.
- `MetaSelectionType`: `PRIMARY`, `CLIPBOARD`, `DND`.
- `MetaSelectionSource` public methods: `get_mimetypes`, `read_async/finish`, `is_active`. The class vfuncs are `activated`, `deactivated`, `get_mimetypes`, `read_async`, `read_finish`.
- Nothing returns a client, PID, app id or window. `MetaSelection` itself offers only set/unset owner, `get_mimetypes`, `transfer_async`.

Internals (not reachable from an extension): on Wayland, `data_device_set_selection` wraps the client's `MetaWaylandDataSource` in a `MetaSelectionSourceWayland` and calls `meta_selection_set_owner` (`src/wayland/meta-wayland-data-device.c`, `meta_wayland_data_device_set_selection`). The wl_client exists in the private struct but is not exposed. Xwayland owners arrive via `src/x11/meta-x11-selection.c` as `MetaSelectionSourceX11`, again with no public accessor.

Two behaviours that matter for a history feature:
- Mutter's own `MetaClipboardManager` (`src/core/meta-clipboard-manager.c`) saves the clipboard when the owner goes away and re-publishes it as a `MetaSelectionSourceMemory`, which triggers a second `owner-changed` with no originating app. A handler that cannot tell this apart from a user copy would see it as a copy made by whatever window is focused then.
- Wayland owner can be a data source created by any client, including a background one (see section 3).

Verdict: No direct way. The signal is a good trigger for "a copy happened"; identity must come from elsewhere (the focus window).

## 3. Focus-window-at-copy heuristic

Mechanism: in the extension, on `owner-changed` for `CLIPBOARD`, read `global.display.focus_window` (`meta_display_get_focus_window`, `src/meta/display.h`) and resolve identity from the window: `get_wm_class()`, `get_gtk_application_id()`, `get_sandboxed_app_id()` (`src/meta/window.h` lines ~162-174), or `Shell.WindowTracker.get_default().get_window_app(win).get_id()` for the desktop-file id (https://gjs.guide/extensions/ , Shell API).

Why it is mostly right: Mutter only accepts `wl_data_device.set_selection` from the client that has keyboard focus. `data_device_set_selection` returns early and cancels the source when `wl_resource_get_client(resource) != data_device->focus_client`; `focus_client` is the client of the keyboard-focused surface set by `meta_wayland_data_device_set_focus` (`src/wayland/meta-wayland-data-device.c`, ~lines 1151 and 1336-1345). So for a Wayland-native selection set through the core protocol, the owner is the client of the focused surface at that moment.

Limits and failure cases (grounded in the code above unless marked):
- Focus is per client, not per window. If the focused surface belongs to the same client as another window, the focus window still maps to the right app. But a client with a focus surface that is not a toplevel (popup, layer-shell, the Shell's own UI) gives `focus_window == null` or a Shell-owned surface.
- Delay between the owner change and your handler. `owner-changed` is synchronous inside Mutter, so reading `focus_window` in the signal handler is current. Reading it after an `await` (reading the content is async) is racy: focus can move in between. Pano reads it before awaiting; Clipboard Indicator reads it in the handler body before its async read. Treat this as a rule: capture the window synchronously.
- Copy from the app while a different window has focus: impossible via the core protocol (rejected above), so not a failure for Wayland-native clients. It is possible via other paths:
  - Xwayland clients: the selection is bridged by Mutter's X11 selection code (`src/x11/meta-x11-selection.c`) and X11 has no keyboard-focus gate. An X11 client can take CLIPBOARD while in the background, and `focus_window` then points at an unrelated window. (Inference from the X11 selection protocol; the code above shows no focus check on that path.)
  - Clipboard managers and other tools that set the selection: Mutter 51.1 does not implement `wlr-data-control` or `ext-data-control` (no hits in `src/wayland/` or `meson.build`), so Wayland-native background clipboard tools cannot set the selection without focus on GNOME. `wl-copy` (wl-clipboard) is commonly described as opening a brief focused surface on compositors without data-control; not verified here. X11-based managers and Shell extensions (including this Launcher's own paste path, or any extension calling `St.Clipboard.set_text` or `Meta.Selection.set_owner`) bypass the focus gate entirely because they run inside the compositor.
  - The Launcher itself: when the user pastes from history, the Launcher or extension re-sets the selection, producing an `owner-changed` whose focus window is the Launcher or the previous app. This needs a self-copy guard regardless of exclusion (the Launcher already knows `local`; the extension does not).
- Keyboard shortcut copies (Ctrl+C): fine, focus is the app. Programmatic copies from a "Copy" button also have focus (user just clicked it).
- Delayed or background self-copies (an app that copies after a timer, a terminal multiplexer running `wl-copy` while another window is focused, a password manager auto-clear that sets an empty selection): the app that sets the selection must hold keyboard focus at that time for Wayland-native clients; if it does not, the request is dropped and no `owner-changed` happens. If another app has focus at that time and sets it, that app is the owner. So the heuristic stays correct for core-protocol Wayland clients and fails for X11 and in-compositor owners.
- Sandboxed apps (Flatpak): `wm_class` can be the app id or something generic; use `get_sandboxed_app_id()` and `get_gtk_application_id()` first, then `wm_class`. Some Electron/Java apps report generic or changing class names. (Observed pattern, not verified here for every app.)
- Same-process multi-window apps (browsers): the exclusion would apply to all windows of that app, which is usually what the user wants.
- Clearing: an `owner-changed` with `source == null` is an unset, not a copy. The handler should skip it (Mutter's clipboard manager then re-publishes from memory, see section 2).

Verdict: Yes as a heuristic. Strong for Wayland-native copy, weak for Xwayland, clipboard managers and in-Shell owners. It identifies "the focused app when the copy event fired", not "the owner".

## 4. Existing GNOME clipboard extensions

All read from HEAD of the default branch.

**Clipboard Indicator** (https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator)
- Setting `excluded-apps` (`as`), "A list of applications that are excluded from clipboard history" (`schemas/org.gnome.shell.extensions.clipboard-indicator.gschema.xml`). Entries are window class names typed by the user in prefs (`prefs.js`, "Excluded Apps").
- Implementation (`extension.js` ~lines 1054-1057): `Shell.Global.get().display.focusWindow` then `get_wm_class()`; `if (wmClass && EXCLUDED_APPS.includes(wmClass)) return;`. Exact, case-sensitive match. Runs before its `await`, so no focus race.
- Also a "private mode" toggle that stops recording.

**Pano** (https://github.com/oae/gnome-shell-pano)
- Settings `watch-exclusion-list` and `exclusion-list`, edited in prefs (`src/prefs/general/exclusionGroup.ts`, `watchExclusions.ts`).
- Two checks:
  - In `src/utils/clipboardManager.ts` (~lines 157-171), inside the `owner-changed` handler: `display.focusWindow?.get_wm_class()`, case-insensitive match against the list, return early.
  - In `src/extension.ts` `trackWindow()` (~lines 236-250): on `notify::focus-window`, if the focused window is excluded it calls `clipboardManager.stopTracking()`; otherwise restarts tracking after a 300 ms timeout. This is a second, redundant mechanism and adds a 300 ms window after focusing a non-excluded app where tracking is off.
- Also an incognito toggle.

**GPaste** (https://github.com/Keruspe/GPaste)
- No per-app exclusion found. A search of the daemon for `wm_class`, `focus_window` and `exclude` finds none.
- It instead honours a content-side hint: `x-kde-passwordManagerHint` (value `secret`) via `gpaste-sensitive-mime.c`, and has a password item type. This is the cooperative "owner marks its copy as secret" convention used by password managers (KeePassXC and others set it), independent of app identity. On X11 it needs an xfixes workaround because GDK drops non-mimetype target atoms (`src/daemon/gpaste-clipboard-x11-hints.c`; `src/libgpaste/gpaste-daemon/AGENTS.md`). Not verified here: how the hint is read on the Wayland path.

Takeaway: the two extensions that offer app exclusion both use the focus-window heuristic by `wm_class`. Neither uses any Mutter-level owner information because none is exposed.

## 5. Passing the source app from the extension to the Launcher

Current plumbing (`pulsaros-spotlight-launcher/gnome-shell-extension/extension.js`):
- The extension serves `org.gnome.Shell.Extensions.PulsarSpotlight` (method `Paste`) and `es.inled.PulsarosSpotlight.Windows` on the session bus.
- The Rust binary serves `es.inled.PulsarosSpotlight.Control` (method `Hide`, `src/control_service.rs`) which the extension calls with `Gio.DBus.session.call`. The extension already uses this "extension calls the Launcher" direction, so a precedent exists.
- The Launcher records copies in `src/main.rs` (`clipboard.connect_changed`, line ~110) with `zbus 4.4`.

What it would take (options, not a recommendation):
- A. Extension pushes: on `owner-changed` (CLIPBOARD, source non-null), read `focus_window` synchronously, compute an app identity (`gtk_application_id` or sandboxed id or desktop id or `wm_class`), and call a new method on the Control interface, for example `ClipboardOwner(s app_id, s wm_class, t timestamp)`. The Launcher's `connect_changed` handler then needs to match the two events, which are unordered and arrive via different channels (GDK signal vs D-Bus). A short correlation window or a sequence is needed; with the extension's call usually arriving first (Mutter emits before GDK sees the new offer), the Launcher can hold "last owner hint" for a few hundred ms and attach it to the next recorded copy, dropping the copy if the hint is excluded.
- B. Extension filters: extension keeps the exclusion list (GSettings or pushed over D-Bus) and tells the Launcher "skip the next copy" through the same new method. Lower data but same correlation problem.
- C. Launcher pulls: on `connect_changed` the Launcher calls an extension method `GetLastClipboardOwner() -> (s, s, t)`. The extension records the last owner snapshot on each `owner-changed`. Avoids races in one direction (the snapshot exists before the call) but still depends on the snapshot belonging to this copy; compare timestamps or a monotonic counter.
- Common requirements: sync read of focus window in the handler; skip `source == null`; skip owner changes caused by the Launcher/extension's own paste (needs a flag); app identity should prefer ids that survive restarts (desktop id) and fall back to `wm_class`; the Launcher's UI to choose apps can list from the existing `Windows.ListWindows` data or the Shell app list.
- Cost: one new D-Bus method plus a handler of ~20 lines in the extension (GNOME 45-51 API surface is the same here: `global.display.get_selection()`, `focus_window`, the `get_*_app_id` methods), and the matching/guard logic in Rust. Needs the extension installed and enabled, so the Launcher must handle "extension absent" (no source info available, exclusion silently off).

## Open questions (not answered by primary sources)

- Whether `get_gtk_application_id()` / `get_sandboxed_app_id()` are populated for the apps the user wants to exclude (browsers, password managers, terminals); only testable per app on a GNOME 48 and 51 session.
- Exact ordering of the extension's `owner-changed` versus GDK `changed` in the Launcher process on GNOME 48 and 51. Mutter emits first by construction, but the Launcher sees a wl_data_device event only after a round trip; measure before relying on ordering.
- Behaviour of Xwayland copies from background X11 apps was inferred from the X11 selection model, not run.

## Sources

- GDK clipboard: https://docs.gtk.org/gdk4/class.Clipboard.html
- Wayland data device protocol: https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_data_device
- Mutter (read at 51.1): https://gitlab.gnome.org/GNOME/mutter, files `src/meta/meta-selection.h`, `src/meta/meta-selection-source.h`, `src/core/meta-selection.c`, `src/core/meta-clipboard-manager.c`, `src/wayland/meta-wayland-data-device.c`, `src/x11/meta-x11-selection.c`, `src/meta/window.h`, `src/meta/display.h`
- GNOME Shell extension guide: https://gjs.guide/extensions/
- Clipboard Indicator: https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator (`extension.js`, `prefs.js`, gschema)
- Pano: https://github.com/oae/gnome-shell-pano (`src/utils/clipboardManager.ts`, `src/extension.ts`)
- GPaste: https://github.com/Keruspe/GPaste (`src/libgpaste/gpaste-daemon/gpaste-sensitive-mime.c`, `src/daemon/gpaste-clipboard-x11-hints.c`)
- Repo: `pulsaros-spotlight-launcher/gnome-shell-extension/extension.js`, `pulsaros-spotlight-launcher/src/main.rs`, `pulsaros-spotlight-launcher/src/control_service.rs`
