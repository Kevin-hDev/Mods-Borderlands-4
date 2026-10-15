"""The window's « ? » (Kevin, 2026-10-14: « notre pastille "?", la même que dans le menu de BL4 Arena, au clic un pop
up avec des explications, elles devront expliquer un peu comment se déroule un run »): beside START, and beside STOP
while a run goes on, each opening the same help pop-up of our windows' shared kind (panel_popup.py), which a click
beside it, its CLOSE button or Escape close alone, never the window. Its look is BL4 Arena's (panel_helps.py), copied as
It Follows keeps its own code (decision 45).

A second help, the Hardcore's (decision 89, spec-hardcore.md, section 5), opens from the « ? » of its row on the
NORMAL MODE page: what the game's levels do, what the Hardcore does, and that it can be paused or switched off."""

from typing import Any

from . import panel_buttons as b, panel_i18n as i18n, panel_popup, panel_text as tx, panel_theme as t
from . import panel_widgets as w, report

# Each help's pop-up, by its key, and the « ? » that open it: the run's beside START and beside STOP while a run goes
# on, the Hardcore's on its row. Its title and sentences are the texts <key>_title and <key>.
HELPS = {"help_run": ("run_help", "live_help"), "help_hardcore": ("hardcore_help",)}


def button(owner: Any, widgets: dict, name: str, template: Any) -> Any:
    """A « ? » in the look of our windows' other ones: small, ink, orange."""
    body = b.button(owner, widgets, name, "lang", template, "secondary")
    widgets[f"{name}_label"].SetText("?")
    return body


def build(widgets: dict, template: Any) -> None:
    """The helps' pop-ups, closed, in the window's pop-up layer."""
    for key in HELPS:
        content = panel_popup.build(widgets, key, template)
        widgets[f"help:{key}"] = tx.text(content, "", "body", wrap=True)
        w.column(content, widgets[f"help:{key}"], padding=w.pad(t.SPACE_2, 0, t.SPACE_2))


def poll(form: Any, widgets: dict) -> bool:
    """A « ? » clicked opens its help; whether one was. Every « ? » is read, so that none keeps a click for later."""
    clicked = [key for key, names in HELPS.items() if any([form.take(widgets[name]) for name in names])]
    if not clicked:
        return False
    key, language = clicked[0], form.model.language
    widgets[f"heading:popup_{key}"].SetText(i18n.text(f"{key}_title", language))
    widgets[f"group:popup_{key}"].SetText("")
    widgets[f"help:{key}"].SetText(i18n.text(key, language))
    panel_popup.show(form, widgets, key)
    report.note("help_shown", help=key)
    return True
