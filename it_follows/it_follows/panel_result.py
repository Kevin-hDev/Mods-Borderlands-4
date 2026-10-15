"""A run's result over the whole window (decision 63; sketch 5 of esquisses_menu, validated by Kevin): its title, how it
ended, a sentence with the time held and the level, its kills, deaths and time, then HISTORY and CLOSE. Shown when the
window opens by itself at the end of the run's time, after STOP, and at the next opening after a run that stopped by
itself (ending.py); remembered as shown once it shows.

HISTORY closes it on the HISTORY page, the run on top; CLOSE, or Escape, closes it alone."""

from typing import Any

from . import ending, history, panel_buttons as b, panel_figures as figures, panel_i18n as i18n
from . import panel_overlay as overlay, panel_text as tx, panel_theme as t, panel_widgets as w, panel_words as words
from . import report, texts

KEY = "result"


def build(widgets: dict, template: Any) -> None:
    rows = overlay.build(widgets, KEY, t.RESULT_WIDTH)
    widgets["result_sentence"] = tx.text(rows, "", "lead", wrap=True)
    w.column(rows, widgets["result_sentence"], padding=w.pad(t.SPACE_3, 0, t.SPACE_4))
    w.column(rows, figures.build(rows, widgets, "result"))
    foot = w.new("HorizontalBox", rows)
    w.row(foot, w.new("Spacer", foot), fill=True)
    w.row(foot, b.button(foot, widgets, "result_history", "action", template, "secondary"), valign="Center",
          padding=w.pad(0, t.SPACE_5, 0, 0))
    w.row(foot, b.button(foot, widgets, "result_close", "action", template, "primary"), valign="Center")
    w.column(rows, foot, padding=w.pad(t.SPACE_5, 0, 0))


def paint(form: Any, widgets: dict, language: str) -> None:
    run = getattr(form, "result", None)
    if run is None:
        return
    widgets[f"heading:{KEY}"].SetText(i18n.text(f"result:{run.end}", language))
    widgets[f"group:{KEY}"].SetText("")
    widgets["result_sentence"].SetText(i18n.text(f"result_sentence:{run.end}", language).format(
        held=texts.clock(run.played_s), level=words.level_in_sentence(run.level, language)))
    figures.paint(widgets, "result", language, run.kills, run.deaths, run.played_s, None)
    widgets["result_history_label"].SetText(i18n.text("history", language))
    widgets["result_close_label"].SetText(i18n.text("close", language))


def open_waiting(form: Any, widgets: dict) -> bool:
    """The result waiting (ending.py) shown, and remembered as shown; whether there was one."""
    run: history.Run | None = ending.waiting()
    if run is None:
        return False
    ending.shown()
    form.result = run
    paint(form, widgets, form.model.language)
    overlay.show(form, widgets, KEY)
    report.note("result_shown", end=run.end)
    return True


def poll(form: Any, widgets: dict) -> str | bool:
    """While the result shows, its buttons alone: "history" when HISTORY closed it, else whether it shows."""
    if form.popup != KEY:
        return False
    to_history = form.take(widgets["result_history"])
    if to_history or form.take(widgets["result_close"]):
        from . import panel_popup
        panel_popup.hide(form, widgets)
        return "history" if to_history else True
    return True
