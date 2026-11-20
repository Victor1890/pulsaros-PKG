# Can the Spotlight window shrink to a bar and stay placed on GNOME Wayland?

Issue #194 (child of #189). Research only, no product code changed. Nothing here was run on a live GNOME session.

## Question

The launcher window (`pulsaros-spotlight-launcher/src/ui/window.rs`) is fixed at 712x580: default size, `resizable(false)`, `set_size_request`, undecorated, transparent CSS. GNOME places it. The Shell extension only calls `make_above()` and `stick()`. We want it to shrink to a pill-sized bar (about 700x60) and grow back, with the top edge fixed and growth downward.

## Short answer

Yes, very likely. Resize from the app by changing the size request (and the visible content). Do not move the window from the extension.

- On Wayland a client cannot position itself. It only tells the compositor its size (a new buffer plus the xdg-shell min/max size).
- Mutter places a toplevel once, when it first maps. After that it keeps the window's top-left corner and only changes the size. So the top edge stays put and the window grows downward.
- Centering only happens at first placement, and only for dialogs, splash screens, or when the user turned on "center new windows".
- The extension's click-outside check uses the window's frame rectangle. When the window shrinks, the rectangle shrinks, so the click-outside report becomes correct with no change.
- Setting an input region from the app is possible but not needed if the transparent area is removed by shrinking the window itself.

## Evidence

Mutter, window placement and resize (`src/wayland/meta-window-wayland.c`, `src/core/place.c`):

- In the Wayland move/resize path, placement is only calculated when `!window->placed`. If the window is already placed, `has_position = TRUE` and the existing rectangle is reused, so a client size change does not re-run placement.
- `calculate_position()` only shifts the origin for south or east gravity. The default case keeps `x` and `y`. A client-driven resize carries no such gravity (that is for compositor-driven drag resizes).
- `window_place_centered()` is true only for dialog, modal dialog, splash, or a normal window when the `center-new-windows` preference is set. It is used from `meta_window_place`, which runs at first map.
- Sources: https://gitlab.gnome.org/GNOME/mutter/-/blob/main/src/wayland/meta-window-wayland.c and https://gitlab.gnome.org/GNOME/mutter/-/blob/main/src/core/place.c

GTK4 (`gtk/gtkwindow.c`, `gdk/wayland/gdksurface-wayland.c`, `gdk/wayland/gdktoplevel-wayland.c`):

- GTK only sets an input region itself for client-side decorated windows with shadows (`update_realized_window_properties` returns early otherwise). Our window is undecorated, so GTK does not touch the input region and the app is free to set one.
- `gdk_surface_set_input_region()` on Wayland stores the region and applies `wl_surface_set_input_region` on the next commit. The docs say clicks outside the region pass to the surface below, and a NULL region means the whole surface is reactive. Check `gdk_display_supports_input_shapes()` first. Source: https://docs.gtk.org/gdk4/method.Surface.set_input_region.html
- GTK sends the window min and max size to the compositor through `xdg_toplevel.set_min_size` / `set_max_size`. A non-resizable GTK window has min equal to max. Changing the size request updates both, so the compositor sees the new fixed size. Source: https://gitlab.gnome.org/GNOME/gtk/-/blob/main/gdk/wayland/gdktoplevel-wayland.c
- Wayland protocol: `wl_surface.set_input_region` is double-buffered and applies on commit. https://wayland.app/protocols/wayland#wl_surface:request:set_input_region (the page was too long for our fetch tool to read that section, so this line rests on the GTK code above and on my reading of the protocol, not on a fetched quote)

Extension (`pulsaros-spotlight-launcher/gnome-shell-extension/extension.js`):

- The click-outside handler reads `win.get_frame_rect()` on each press and compares it with `isPointOutsideRect`. It never caches the rectangle, so it follows the current size.
- Today the transparent margin inside the 712x580 frame counts as "inside", so clicks there do not dismiss the launcher. That already behaves this way and is not new.

## Options

1. App resizes itself (recommended). Change the size request and default size to about 700x60 when idle and to full size when results show. Keep `resizable(false)`.
   - Pro: no extension change, top-left kept by Mutter once placed, matches how the app already sizes itself.
   - Con: there can be one frame where old content is drawn at the new size. Hide the results area before shrinking and show it after growing.
   - Con: if the window is hidden with `set_visible(false)` and shown again, Mutter may treat it as a new map. Not verified (see below).
2. Keep the window 712x580 and set an input region to the pill only (`gdk_surface_set_input_region`).
   - Pro: no resize, no position risk.
   - Con: the window still covers the area. The extension's frame-rect check says "inside" for clicks that now pass through to other windows, so click-outside would stop firing there. The extension would have to compute the visible rectangle itself. More moving parts than option 1.
3. Extension moves and resizes with `Meta.Window.move_resize_frame(user_op, x, y, w, h)`.
   - Pro: the compositor owns the position.
   - Con: for a Wayland client Mutter sends a configure and the client still decides the final size, so app and extension can fight. It needs a new D-Bus call and splits position logic across two places. Keep it only as a fallback to restore the position if testing shows drift. It is not the primary way to resize.
4. Two windows (a bar and a panel). Rejected: doubles the focus and stacking problems.

## What could not be verified without a live GNOME session

- Whether a client-side shrink or grow really keeps the top edge on the GNOME versions we ship (45 to 51). The source says yes for placed windows, but nobody ran it.
- Whether hide (`set_visible(false)`) then `present()` keeps the old position or re-places the window. The code keeps `window->placed`, but unmap and remap was not traced to the end.
- Whether `center-new-windows` is enabled on user machines (it only affects first placement).
- Flicker or one wrong frame during the resize.
- Whether `gdk_display_supports_input_shapes()` is true on the target setup (it should be on Wayland).
- Whether `move_resize_frame` on a Wayland window is honored without the client reacting.

Suggested check: log `get_frame_rect()` from the extension on `size-changed`, toggle the size three times on GNOME 48 and 51, and also test hide then present.
