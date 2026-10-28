"""The SETTINGS page (sketch A2 of esquisses_mod_companions, decision 68 of docs/renforts): TEAM SETTINGS, the five
settings for every companion alike, each a slider with its value in words (panel_values.py); then OPTIONS: the bars
on the left of the screen, its row shown only while their package lies in the game's Paks (companions/bars.py: the
setting would do nothing without it), and the two keys (panel_keys.py). While the team is on, the five sliders are
greyed under a line saying to stop the team: it keeps the settings it started with (tuning_given.py). While no team
of Companions may start (session.blocked: It Follows leads it, with its own settings), the sliders and the bars'
row are greyed under the line that says why: a row that acts on nothing is greyed (docs/mokup/menu_mods,
decisions.md). The keys stay: they are the window's."""

from typing import Any

from . import panel_i18n as i18n, panel_keys, panel_pages as p, panel_text as tx, panel_theme as t
from . import panel_values, panel_widgets as w, session, settings

KEY = "settings"
OPTIONS = "options"


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def _greyed(widgets: dict, key: str, greyed: bool) -> None:
    widgets[f"setting:{key}"].SetIsEnabled(not greyed)
    for part in ("row", "description"):
        widgets[f"{part}:{key}"].SetRenderOpacity(t.OPACITY_DISABLED if greyed else 1.0)


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    p.setting_rows(rows, settings.TEAM, widgets, template, expose_rows=True)
    widgets["settings_locked"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets["settings_locked"], padding=w.pad(t.SPACE_2, 0))
    p.heading(rows, widgets, OPTIONS)
    widgets["settings_bars_box"] = box = w.new("VerticalBox", rows)
    p.setting_rows(box, [settings.bars], widgets, template, expose_rows=True)
    w.column(rows, box)
    panel_keys.draw(rows, widgets, template)
    return scroll


def paint(form: Any, widgets: dict, language: str) -> None:
    widgets[f"heading:{KEY}"].SetText(i18n.text("team_settings", language))
    widgets[f"heading:{OPTIONS}"].SetText(i18n.text(OPTIONS, language))
    widgets[f"group:{OPTIONS}"].SetText("")
    on, why = session.team_on(), session.blocked()
    for option in settings.TEAM:
        _greyed(widgets, option.identifier, on or why is not None)
        widgets[f"low:{option.identifier}"].SetText(panel_values.number(option, option.min_value))
        widgets[f"high:{option.identifier}"].SetText(panel_values.number(option, option.max_value))
    _greyed(widgets, settings.bars.identifier, why is not None)
    widgets["settings_locked"].SetText(i18n.text("settings_locked" if on or why is None else why, language))
    _visible(widgets["settings_locked"], on or why is not None)
    _visible(widgets["settings_bars_box"], getattr(form, "bars_offered", False))
    panel_keys.paint(widgets, language, blocked=why is not None)
