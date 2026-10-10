"""The window's pop-ups (Kevin, 2026-10-09: the sniper optics' « ? »): a card in the middle of the window over a dim
layer that takes every click beside it. A click beside the card, its CLOSE button or Escape close the pop-up only,
never the window (Kevin: « attention à ce que ça ne ferme pas tout le menu »): while one is open the form polls it
alone, and Escape asks the form first (panel_form_lifecycle.py).

The cards lie in a layer over the whole window (panel_view.py, "popups"), so a page or its scrolling never cuts one.
"""

from . import panel_buttons as b, panel_i18n as i18n, panel_pages as p, panel_theme as t, panel_widgets as w

# The card's width in the window's drawing units: a sentence reads on two or three lines, the card stays well inside
# the smallest window.
WIDTH = 760
# How dark the layer beside the card is, so the card reads as in front of the window.
DIM = 0.6


def _shown(widget, shown):
    # Open, the pop-up's own layers take the clicks, the box holding them never does.
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def build(widgets, key, template):
    """The pop-up `key`, closed, in the window's pop-up layer: returns the box for its content, above its CLOSE
    button. Its title plate and sentence are heading:popup_<key> and group:popup_<key>, written by its owner."""
    layer = widgets["popups"]
    root = w.new("Overlay", layer)
    _shown(root, False)
    w.layer(layer, root)
    widgets[f"popup:{key}"] = root
    beside = w.new("CheckBox", root)
    beside.WidgetStyle.CheckBoxType = b.TOGGLE_BUTTON
    for field, _veil in b._STATES:
        w.style_brush(beside.WidgetStyle, field, template, t.COLOR_INK, alpha=DIM)
    w.layer(root, beside)
    widgets[f"popup:{key}:beside"] = beside
    holder = w.new("VerticalBox", root)
    w.layer(root, w.sized(root, holder, width=WIDTH), halign="Center", valign="Center")
    rows = p.card(holder, widgets, f"popup_{key}")
    content = w.new("VerticalBox", rows)
    w.column(rows, content)
    w.column(rows, b.button(rows, widgets, f"popup:{key}:close", "action", template, "secondary"), halign="Left",
             padding=w.pad(t.SPACE_4, 0, 0))
    return content


def show(form, widgets, key):
    form.popup = key
    widgets[f"popup:{key}:close_label"].SetText(i18n.text("close", form.model.language))
    _shown(widgets[f"popup:{key}"], True)


def hide(form, widgets):
    key, form.popup = form.popup, None
    if key is not None:
        _shown(widgets[f"popup:{key}"], False)


def poll(form, widgets):
    """A click beside the open pop-up or on its CLOSE button shuts it; nothing else of the window can be clicked."""
    clicked = [form.take(widgets[f"popup:{form.popup}:{part}"]) for part in ("beside", "close")]
    if any(clicked):
        hide(form, widgets)
