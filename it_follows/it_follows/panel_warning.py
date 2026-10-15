"""The warning diamond of our menus' mockup (docs/mokup/menu_mods/theme/menu.css, .warn): an orange square turned on
its corner behind a "!", set apart by its shape, not only its colour; and the caution framed in orange that the RUN
page and the welcome say (decisions 54 and 60). Taken from BL4 Arena's panel_warning.py, as It Follows keeps its own
code (decision 45)."""

from typing import Any

from . import panel_text as tx, panel_theme as t, panel_widgets as w


def diamond(owner: Any) -> Any:
    stack = w.new("Overlay", owner)
    frame, _fill = w.framed(stack, t.COLOR_SPARK, t.STROKE_THIN)
    frame.SetRenderTransformAngle(float(t.TILT_WARNING))
    w.layer(stack, frame)
    w.layer(stack, tx.text(stack, "!", "mark", center=True), halign="Center", valign="Center")
    return w.sized(owner, stack, t.WARNING_SIZE, t.WARNING_SIZE)


def caution(owner: Any, widgets: dict, name: str) -> Any:
    """A caution framed in orange: the diamond and its words, registered as name; returns the frame."""
    frame, fill = w.framed(owner, t.COLOR_CARD, t.STROKE, w.pad(t.SPACE_4, t.SPACE_5), frame=t.COLOR_SPARK)
    line = w.new("HorizontalBox", fill)
    w.row(line, diamond(line), padding=w.pad(t.SPACE_1, 0, 0), valign="Top")
    widgets[name] = tx.text(line, "", "body", wrap=True)
    w.row(line, widgets[name], fill=True, padding=w.pad(0, 0, 0, t.SPACE_4), valign="Center")
    fill.SetContent(line)
    return frame
