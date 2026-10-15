"""A card over the whole window, on a dim veil, in its pop-up layer (panel_view.py, "popups"): the welcome and a run's
result. Built as BL4 Arena's welcome, with its own buttons instead of the pop-up's CLOSE; a click beside it does
nothing, so that a stray click never takes away what the player has to read. While it shows it is the form's open
pop-up: Escape closes it alone (panel_form_lifecycle.py, panel_popup.hide)."""

from typing import Any

from . import panel_pages as p, panel_theme as t, panel_widgets as w

# How dark the veil beside the card is: the ink at 65 %, as BL4 Arena's welcome.
DIM = 0.65


def build(widgets: dict, key: str, width: int) -> Any:
    """The card `key`, closed: returns its rows, under its title plate heading:<key> and its sentence group:<key>."""
    root = w.new("Overlay", widgets["popups"])
    root.SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    w.layer(widgets["popups"], root)
    widgets[f"popup:{key}"] = root
    veil = w.border(root, t.COLOR_INK, alpha=DIM)
    veil.SetVisibility(w.enum("ESlateVisibility", "Visible"))  # takes the clicks beside the card, which do nothing
    w.layer(root, veil)
    holder = w.new("VerticalBox", root)
    w.layer(root, w.sized(root, holder, width=width), halign="Center", valign="Center")
    return p.card(holder, widgets, key)


def show(form: Any, widgets: dict, key: str) -> None:
    form.popup = key
    widgets[f"popup:{key}"].SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible"))
