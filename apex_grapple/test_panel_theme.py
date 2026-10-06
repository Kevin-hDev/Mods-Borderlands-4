"""Themes change colours only, read when the window is drawn: no EMBER colour stays in another theme's window."""

import sys
from types import SimpleNamespace as NS
import panel_render_fixture as fixture
from apex_grapple import panel_fonts, panel_form, panel_factory, panel_model, panel_preferences, panel_view
from apex_grapple import panel_buttons as b, panel_theme as t, panel_widgets as w

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


# The hover and press veils are the same white and black in every theme.
VEILS = {(t.HOVER_OVERLAY[0], t.HOVER_OVERLAY[1]), (t.PRESS_OVERLAY[0], t.PRESS_OVERLAY[1])}


def drawn(theme):
    """Every (colour, opacity) a window opened in `theme` paints: all colours pass through panel_theme.rgba."""
    fixture.install()
    panel_preferences.theme.value = theme
    model = panel_model.Model(fixture.pf.f.mod)
    used, original = [], t.rgba
    t.rgba = lambda hex_color, alpha=1.0: used.append((hex_color, alpha)) or original(hex_color, alpha)
    try:
        root, widgets = panel_view.build_view(NS(), model)
        refs = {name: lambda widget=widget: widget for name, widget in widgets.items()}
        form = panel_form.PanelForm(refs, panel_factory.PanelBindings(), model)
    finally:
        t.rgba = original
    return set(used), widgets, form


panel_fonts.build = lambda outer: {}
check(t.THEMES == ("EMBER", "DARK", "LIGHT", "BL4"), "Kevin's four themes, in the order the button walks them")
check(set(t.PALETTES) == set(t.THEMES), "Each theme has its palette")
check(all(name.startswith("COLOR_") and hasattr(t, name) for palette in t.PALETTES.values() for name in palette),
      "A palette only changes existing colours, never sizes, fonts or shapes")
for theme in t.THEMES:
    used, widgets, form = drawn(theme)
    palette = {name: value for name, value in vars(t).items() if name.startswith("COLOR_")}
    check(palette == {**t._EMBER, **t.PALETTES[theme]}, f"{theme}: use() puts the whole palette in place")
    stray = {(colour, alpha) for colour, alpha in used
             if colour not in palette.values() and (colour, alpha) not in VEILS}
    check(not stray, f"{theme}: colours kept from another theme: {sorted(stray)}")
    label = widgets["theme_label"].text
    check(label.startswith("THEME: ") and label.split(": ")[1] == {"EMBER": "EMBER", "DARK": "DARK",
                                                                   "LIGHT": "LIGHT", "BL4": "BL4"}[theme],
          f"{theme}: the header button names the open theme")
    check(form.redraw is False, f"{theme}: opening asks for no second drawing")
# A colour kept from loading would show here: the light theme draws the EMBER window colour nowhere.
used, widgets, _form = drawn("LIGHT")
check(not any(colour == "1e0906" for colour, _alpha in used), "The light window is not drawn in EMBER's red")
check(("8a6400", 1.0) in used, "Gold text on a light card turns dark amber")
check(widgets["FR_fill"].brush == w.linear("f7f3eb") and widgets["FR_label"].color == w.slate("66574a"),
      "A light off button is cream with a dark label: beige on a black box would not read")
check(widgets["first:key_label"].color == w.slate("ffd21f"), "A key's name stays gold on its ink selector")


def contrast(first, second):
    light, dark = sorted((t.luminance(first), t.luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


# Each button's label against what shows behind it, in every theme. The frame is a whole box under the fill: over a
# transparent fill it showed in the label's colour and hid every light-theme label (Kevin's screenshot, 2026-10-06).
for theme in t.THEMES:
    t.use(theme)
    for style in b.STYLES:
        fill, frame, text, _shadow = b.colours(style)
        check(fill is not None or frame is None, f"{theme} {style}: a transparent fill over a coloured frame")
        # The one transparent button, a sidebar page, lies on the sidebar.
        behind = fill or t.COLOR_SIDEBAR
        check(contrast(text, behind) >= 4.5, f"{theme} {style}: label {text} unreadable on {behind}")
t.use("LIGHT")
check(t.on_card("38f0f0") == "1c7878", "A pale class colour is halved on a light card")
t.use("DARK")
check(t.on_card("38f0f0") == "38f0f0", "On a dark card the class colour stays as the game shows it")
t.use("no such theme")
check(t.current() == "EMBER" and t.COLOR_WINDOW == "1e0906", "An unknown saved name draws EMBER")
_, widgets, form = drawn("EMBER")
widgets["FR"].checked = True
form.poll()
check(widgets["theme_label"].text == "THÈME : BRAISE", "French names the theme in French")
panel_preferences.theme.value = "EMBER"

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | themes: whole palettes, drawn colours only, names, fallback")
sys.exit(1 if failures else 0)
