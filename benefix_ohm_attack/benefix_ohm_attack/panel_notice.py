# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""The sentence at the top of a page, above its rows and always in view, in an orange slanted frame: the heirloom's
settings wait for the next weapon change (Kevin, 2026-09-26, sketch A, cosmetics/heirloom/docs/esquisses_menu/A.png).
Which page says what is menu.NOTICES; the labels write it, in capitals as the sketch did.
"""

from . import panel_text as tx, panel_theme as t, panel_widgets as w


def notice(rows, widgets, key):
    frame, fill = w.framed(rows, t.COLOR_CARD, t.STROKE, w.pad(t.SPACE_2, t.SPACE_4), frame=t.COLOR_SPARK)
    widgets[f"notice:{key}"] = tx.text(fill, "", "status", wrap=True)
    fill.SetContent(widgets[f"notice:{key}"])
    w.column(rows, w.slant(frame), padding=w.pad(t.SPACE_3, 0, t.SPACE_1, t.SPACE_1), halign="Left")
