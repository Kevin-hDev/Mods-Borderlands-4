"""The header's THEME button: each click saves the following theme, then the window is drawn again in its colours.

One implementation for every window, Grapple's and Movement's alike (Kevin, 2026-10-06: BRAISE, SOMBRE, CLAIR, BL4).
"""

from . import panel_buttons as b, panel_i18n as i18n, panel_theme as t


def following(theme):
    return t.THEMES[(t.THEMES.index(theme) + 1) % len(t.THEMES)] if theme in t.THEMES else t.THEMES[0]


def choose(form, widgets):
    """Ignored during a key capture, which a new window would drop; control_window_redraw draws the new one."""
    if form.selecting():
        return
    if form.flush(widgets) and form.model.change_theme(following(form.model.theme)):
        form.redraw = True
    else:
        form.report(widgets, "failed")


def paint(widgets, theme, language):
    widgets["theme_label"].SetText(f"{i18n.text('theme', language)} {i18n.text(f'theme:{theme}', language)}")
    b.paint(widgets, "theme", "lang_off")
