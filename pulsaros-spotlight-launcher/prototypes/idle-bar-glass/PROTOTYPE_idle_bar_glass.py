#!/usr/bin/env python3
"""PROTOTYPE, throwaway. Wayfinder ticket: "What are the pill and button glass tokens?"

Question: what should the Spotlight idle bar pill and the four round buttons look like in GTK4 CSS
with NO compositor blur, judged against ~/Pictures/spotlight/idle.png and idle-btn.png?

Three structurally different glass treatments, switchable at the bottom:
  A  Flat tint       translucent fill, hairline edge, neutral soft shadow
  B  Specular glass  vertical gradient + inset top highlight + wallpaper-tinted shadow (Tahoe look)
  C  Frosted solid   near-opaque fill, no highlight, tiny shadow (legibility first, no blur needed)

Keys:  Left/Right variant   L light/dark   M buttons on/off (Idle <-> IdleWithModes)
       B background (soft gradient / busy dark / white)   Esc quit
Run:   python3 PROTOTYPE_idle_bar_glass.py
"""
import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

VARIANTS = ["A  Flat tint", "B  Specular glass", "C  Frosted solid"]
BACKGROUNDS = [
    ("soft gradient", "linear-gradient(160deg, #8fb4e8 0%, #b9c6f0 40%, #f1c7c0 100%)"),
    ("busy dark", "linear-gradient(45deg, #1b1f3a 0%, #7a2e5d 35%, #1d6b72 65%, #c9a227 100%)"),
    ("white", "#f4f4f6"),
]

# colours: (fill, edge, shadow, text, disc_fill, disc_edge, highlight)


def glass_css(v, dark):
    ink = "#f2f4fb" if dark else "#1f2a44"
    sub = "rgba(242,244,251,0.65)" if dark else "rgba(31,42,68,0.60)"
    if v == 0:  # flat tint
        fill = "rgba(34,36,50,0.55)" if dark else "rgba(255,255,255,0.55)"
        edge = "rgba(255,255,255,0.22)" if dark else "rgba(255,255,255,0.70)"
        shadow = "0 8px 24px rgba(0,0,0,0.28)" if dark else "0 8px 24px rgba(20,30,70,0.18)"
        disc = fill
        extra = ""
    elif v == 1:  # specular
        if dark:
            fill = "linear-gradient(to bottom, rgba(70,74,96,0.62), rgba(30,32,46,0.42))"
            edge = "rgba(255,255,255,0.28)"
            shadow = "0 10px 28px rgba(10,12,40,0.45)"
            hi = "inset 0 1px 0 rgba(255,255,255,0.40), inset 0 -1px 0 rgba(255,255,255,0.08)"
        else:
            fill = "linear-gradient(to bottom, rgba(255,255,255,0.78), rgba(255,255,255,0.34))"
            edge = "rgba(255,255,255,0.80)"
            shadow = "0 10px 28px rgba(70,100,200,0.32)"
            hi = "inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.35)"
        disc = fill
        extra = hi
    else:  # frosted solid
        fill = "rgba(44,46,62,0.90)" if dark else "rgba(242,245,255,0.90)"
        edge = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.06)"
        shadow = "0 2px 10px rgba(0,0,0,0.30)" if dark else "0 2px 10px rgba(0,0,0,0.15)"
        disc = "rgba(60,63,84,0.92)" if dark else "rgba(228,233,250,0.94)"
        extra = ""
    inset = f", {extra}" if extra else ""
    return f"""
    .pill {{
        border-radius: 999px; min-height: 60px; padding: 0 22px;
        background: {fill}; border: 1px solid {edge};
        box-shadow: {shadow}{inset};
    }}
    .pill image {{ -gtk-icon-size: 24px; color: {sub}; }}
    .pill label.hint {{ font-size: 24px; font-weight: 300; color: {sub}; }}
    button.disc {{
        border-radius: 999px; min-width: 60px; min-height: 60px; padding: 0;
        background: {disc}; border: 1px solid {edge}; color: {ink};
        box-shadow: {shadow}{inset};
    }}
    button.disc image {{ -gtk-icon-size: 26px; }}
    button.disc:hover {{ background: {disc}; border-color: {ink}; }}
    """


BASE_CSS = """
window.proto { background: transparent; }
.stage { background-size: cover; }
.switcher {
    background: rgba(15,15,18,0.92); color: #fff; border-radius: 999px;
    padding: 6px 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.switcher label { color: #fff; font-weight: 600; }
"""

ICONS = [
    "view-app-grid-symbolic",
    "folder-symbolic",
    "applications-system-symbolic",
    "edit-paste-symbolic",
]


class Proto(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="PROTOTYPE idle bar glass")
        self.set_default_size(820, 420)
        self.add_css_class("proto")
        self.variant, self.dark, self.modes, self.bg = 1, False, False, 0
        self.base = Gtk.CssProvider()
        self.base.load_from_string(BASE_CSS)
        self.glass = Gtk.CssProvider()
        self.bgp = Gtk.CssProvider()
        disp = Gdk.Display.get_default()
        for p in (self.base, self.glass, self.bgp):
            Gtk.StyleContext.add_provider_for_display(
                disp, p, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        overlay = Gtk.Overlay()
        self.stage = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stage.add_css_class("stage")
        overlay.set_child(self.stage)
        self.set_child(overlay)

        # the bar: pill (shrinks) + four discs (revealed)
        self.row = Gtk.Box(spacing=12)
        self.row.set_halign(Gtk.Align.CENTER)
        self.row.set_valign(Gtk.Align.CENTER)
        self.row.set_vexpand(True)
        self.row.set_size_request(740, -1)
        pill = Gtk.Box(spacing=12)
        pill.add_css_class("pill")
        pill.set_hexpand(True)
        pill.set_valign(Gtk.Align.CENTER)
        pill.append(Gtk.Image.new_from_icon_name("system-search-symbolic"))
        hint = Gtk.Label(label="Spotlight Search")
        hint.add_css_class("hint")
        hint.set_xalign(0)
        pill.append(hint)
        self.row.append(pill)
        self.discs = []
        for name in ICONS:
            b = Gtk.Button()
            b.add_css_class("disc")
            b.set_child(Gtk.Image.new_from_icon_name(name))
            b.set_valign(Gtk.Align.CENTER)
            b.set_focusable(False)
            self.row.append(b)
            self.discs.append(b)
        self.stage.append(self.row)

        # switcher
        sw = Gtk.Box(spacing=12)
        sw.add_css_class("switcher")
        sw.set_halign(Gtk.Align.CENTER)
        sw.set_valign(Gtk.Align.END)
        sw.set_margin_bottom(14)
        self.label = Gtk.Label()
        prev, nxt = Gtk.Button(label="◀"), Gtk.Button(label="▶")
        prev.connect("clicked", lambda *_: self.step(-1))
        nxt.connect("clicked", lambda *_: self.step(1))
        for w in (prev, self.label, nxt):
            sw.append(w)
        overlay.add_overlay(sw)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self.on_key)
        self.add_controller(key)
        self.render()

    def step(self, d):
        self.variant = (self.variant + d) % len(VARIANTS)
        self.render()

    def on_key(self, _c, keyval, _code, _state):
        name = Gdk.keyval_name(keyval)
        if name == "Left":
            self.step(-1)
        elif name == "Right":
            self.step(1)
        elif name in ("l", "L"):
            self.dark = not self.dark
            self.render()
        elif name in ("m", "M"):
            self.modes = not self.modes
            self.render()
        elif name in ("b", "B"):
            self.bg = (self.bg + 1) % len(BACKGROUNDS)
            self.render()
        elif name == "Escape":
            self.close()
        return True

    def render(self):
        self.glass.load_from_string(glass_css(self.variant, self.dark))
        self.bgp.load_from_string(
            ".stage { background: %s; }" % BACKGROUNDS[self.bg][1])
        for d in self.discs:
            d.set_visible(self.modes)
        self.label.set_label(
            f"{VARIANTS[self.variant]}  |  {'dark' if self.dark else 'light'}  |  "
            f"{'IdleWithModes' if self.modes else 'Idle'}  |  bg: {BACKGROUNDS[self.bg][0]}"
        )


def main():
    app = Gtk.Application(application_id="es.inled.PrototypeIdleBarGlass")
    app.connect("activate", lambda a: Proto(a).present())
    app.run(None)


if __name__ == "__main__":
    main()
