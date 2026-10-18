"""A run's three counts as the sketches draw them (esquisses_menu, images 2 and 5): KILLS, DEATHS and TIME, each a small
caption over a big figure, the time limit beside the time when the run has one. The run in progress (panel_run.py)
and the result of the last one (panel_result.py) show them alike."""

from typing import Any

from . import panel_i18n as i18n, panel_text as tx, panel_theme as t, panel_widgets as w, texts

NAMES = ("kills", "deaths", "time")


def build(owner: Any, widgets: dict, prefix: str) -> Any:
    """The three counts side by side, registered as <prefix>:<name> and <prefix>:<name>_caption, the limit as
    <prefix>:limit."""
    line = w.new("HorizontalBox", owner)
    for name, width in zip(NAMES, t.FIGURE_WIDTHS):
        column = w.new("VerticalBox", line)
        widgets[f"{prefix}:{name}_caption"] = tx.text(column, "", "caption")
        w.column(column, widgets[f"{prefix}:{name}_caption"])
        figures = w.new("HorizontalBox", column)
        widgets[f"{prefix}:{name}"] = tx.text(figures, "", "figure")
        w.row(figures, widgets[f"{prefix}:{name}"], valign="Bottom")
        if name == "time":
            widgets[f"{prefix}:limit"] = tx.text(figures, "", "out")
            w.row(figures, widgets[f"{prefix}:limit"], padding=w.pad(0, 0, t.SPACE_1, t.SPACE_3), valign="Bottom")
        w.column(column, figures)
        w.row(line, w.sized(line, column, width=width), valign="Center")
    return line


def paint(widgets: dict, prefix: str, language: str, kills: int, deaths: int, played_s: float,
          limit_s: float | None) -> None:
    for name in NAMES:
        widgets[f"{prefix}:{name}_caption"].SetText(i18n.text(name, language))
    widgets[f"{prefix}:kills"].SetText(str(kills))
    widgets[f"{prefix}:deaths"].SetText(str(deaths))
    widgets[f"{prefix}:time"].SetText(texts.clock(played_s))
    widgets[f"{prefix}:limit"].SetText("" if limit_s is None else f"/ {texts.clock(limit_s)}")
