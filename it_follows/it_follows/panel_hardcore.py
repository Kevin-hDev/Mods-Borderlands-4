"""The Hardcore's tag in the window's side column, above the version (decision 89, spec-hardcore.md, section 5):
« HARDCORE 7% », and paused said on a second line, while the Hardcore is on; away while it is off. It never says
what rises (Kevin: « sans indiquer exactement ce que le mode hardcore augmente »). It sat right of the author's
name until Kevin's screenshot of 2026-10-23: the header's line had no room for it beside a fourth language's
button. The side column is generated: docs/RUN/outils/menu_window.py writes the call to badge in it."""

from typing import Any

from . import panel_i18n as i18n, panel_text as tx, panel_theme as t, panel_widgets as w
from .normal import hardcore


def badge(owner: Any, widgets: dict) -> None:
    """The tag in the side column, in the look of the cards' orange title plates, at the master button's margin."""
    plate, fill = w.framed(owner, t.COLOR_SPARK, t.STROKE, w.pad(tx.inset(t.SPACE_1, "plate"), t.SPACE_4))
    widgets["hardcore_badge"] = tx.text(fill, "", "plate")
    fill.SetContent(widgets["hardcore_badge"])
    widgets["hardcore_badge_box"] = plate
    w.column(owner, w.slant(plate), halign="Left", padding=w.pad(0, t.SPACE_4))


def paint(widgets: dict, language: str) -> None:
    state = hardcore.state()
    text = i18n.text("hardcore_badge_paused" if state == "paused" else "hardcore_badge", language)
    widgets["hardcore_badge"].SetText(text.format(percent=hardcore.percent()))
    widgets["hardcore_badge_box"].SetVisibility(w.enum("ESlateVisibility",
                                                       "Collapsed" if state == "off" else "HitTestInvisible"))
