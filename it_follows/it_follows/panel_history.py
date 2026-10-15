"""The HISTORY page (sketch 3 of esquisses_menu, validated by Kevin; decision 49): the last 20 runs, most recent on top,
each on a line: when it began, its level, the time limit chosen, the time held, the kills, the deaths, and how it
ended. Its 20 lines are built with the window and filled again at each paint, a line without a run hidden; with no
run yet, a sentence says where they will be."""

from typing import Any

from . import history, kept, panel_i18n as i18n, panel_pages as p, panel_text as tx, panel_theme as t
from . import panel_widgets as w, panel_words as words, texts

# The columns, their header's words and their text's kind; the end fills what the others leave.
COLUMNS = (("when", "col_when", "label"), ("level", "col_level", "label"), ("limit", "col_limit", "label"),
           ("held", "col_held", "value"), ("kills", "col_kills", "value"), ("deaths", "col_deaths", "value"),
           ("end", "col_end", "meta"))


def _line(owner: Any, widgets: dict, name: str, role: str) -> Any:
    """One line of the table, its cells registered as <name>:<column>, in the role given or else each column's own;
    the counts centred in their column."""
    line = w.new("HorizontalBox", owner)
    for (column, _words, kind), width in zip(COLUMNS, (*t.HISTORY_COLUMNS, None)):
        cell = widgets[f"{name}:{column}"] = tx.text(line, "", role or kind, center=kind == "value")
        if width is None:
            w.row(line, cell, fill=True, valign="Center")
        else:
            w.row(line, w.sized(line, cell, width=width), valign="Center")
    return line


def page(owner: Any, _group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    w.column(rows, _line(rows, widgets, "history_head", "caption"), padding=w.pad(t.SPACE_3, 0, t.SPACE_1))
    for index in range(history.MAX_RUNS):
        w.column(rows, w.line(rows, t.COLOR_HOVER, height=t.STROKE_THIN))
        widgets[f"history_line:{index}"] = _line(rows, widgets, f"history:{index}", "")
        w.column(rows, widgets[f"history_line:{index}"], padding=w.pad(t.SPACE_1, 0))
    widgets["history_empty"] = tx.text(rows, "", "desc", wrap=True)
    w.column(rows, widgets["history_empty"], padding=w.pad(t.SPACE_4, 0, t.SPACE_2))
    return scroll


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def cells(run: history.Run, language: str) -> dict[str, str]:
    """A run's line as the table writes it."""
    return {"when": words.when(run.when, language), "level": words.level(run.level, language),
            "limit": words.limit(run.limit_s, language), "held": texts.clock(run.played_s),
            "kills": str(run.kills), "deaths": str(run.deaths), "end": words.end(run.end, language)}


def paint(widgets: dict, language: str) -> None:
    widgets["heading:history"].SetText(i18n.text("history_title", language))
    widgets["group:history"].SetText("")
    for column, header, _kind in COLUMNS:
        widgets[f"history_head:{column}"].SetText(i18n.text(header, language))
    runs = kept.runs()
    for index in range(history.MAX_RUNS):
        shown = index < len(runs)
        _visible(widgets[f"history_line:{index}"], shown)
        if shown:
            for column, text in cells(runs[index], language).items():
                widgets[f"history:{index}:{column}"].SetText(text)
    _visible(widgets["history_empty"], not runs)
    widgets["history_empty"].SetText(i18n.text("history_empty", language))
