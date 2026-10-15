"""The NORMAL MODE page (decision 80, spec-mode-normal.md, section 2): the mode's card, its sentence beside the title,
its rows (the level, whose help is the chosen level's sentence, and the allied enemies) and START across it; while the
mode is on, above it the mode's card with STOP, saying whether it plays or waits for a game, and the rows locked under
a line that says to stop the mode to change them; while a Horde run goes on, START replaced by a line that says to stop
the run first.

START writes the choice to be on in the settings file before the mode starts, and writes it back off when the start is
refused: the file and the mode agree, and the mode comes back at the next launch only if it was on. In a game the mode
plays and START closes the window, as the Horde's does; without one (the main menu, a vehicle) the mode waits for it and
the window stays, saying so. STOP writes the choice off, then stops the mode.

Under it, the Hardcore's card (decision 89, spec-hardcore.md, section 5), which the mode on never locks: its switch
with the « ? » of its help, and its progress, shown only while the Hardcore is on."""

from typing import Any

from . import game_pause, panel_buttons as b, panel_choices, panel_help as help_, panel_i18n as i18n
from . import panel_pages as p, panel_text as tx, panel_theme as t, panel_widgets as w, report, session
from .normal import options as normal_options

KEY = "normal"
# The Hardcore's card, on the same page.
HARDCORE = "hardcore"
# What a start refused says in the footer, by session.start_normal's answer.
REFUSALS = {"horde_running": "start_horde_running", "already_on": "start_already_on", "coop": "start_coop",
            "start_failed": "normal_start_failed"}


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    widgets["normal_live_box"] = live = w.new("VerticalBox", body)
    w.column(body, live)
    rows = p.card(live, widgets, "normal_live")
    line = w.new("HorizontalBox", rows)
    widgets["normal_live_text"] = tx.text(line, "", "body", wrap=True)
    w.row(line, widgets["normal_live_text"], fill=True, valign="Center")
    stop = b.button(line, widgets, "normal_stop", "launch", template, "stop")
    w.row(line, w.sized(line, stop, width=t.STOP_WIDTH), padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, t.SPACE_2))
    rows = p.card(body, widgets, key)
    widgets["normal_locked"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets["normal_locked"], padding=w.pad(t.SPACE_2, 0))
    p.setting_rows(rows, normal_options.LOCKED, widgets, template, expose_rows=True)
    widgets["normal_blocked"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets["normal_blocked"], padding=w.pad(t.SPACE_5, 0, t.SPACE_2))
    widgets["normal_start_box"] = line = w.new("HorizontalBox", rows)
    w.row(line, b.button(line, widgets, "normal_start", "launch", template, "primary"), fill=True, valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_5, 0, t.SPACE_2))
    rows = p.card(body, widgets, HARDCORE)
    p.setting_rows(rows, [normal_options.hardcore], widgets, template, expose_rows=True)
    line = widgets[f"row:{normal_options.hardcore.identifier}"]
    w.row(line, help_.button(line, widgets, "hardcore_help", template), padding=w.pad(0, 0, 0, t.SPACE_3),
          valign="Center")
    widgets["hardcore_progress_box"] = box = w.new("VerticalBox", rows)
    w.column(rows, box)
    p.setting_rows(box, [normal_options.progress], widgets, template, expose_rows=True)
    return scroll


def paint(form: Any, widgets: dict, language: str) -> None:
    live = session.normal_live()
    form.normal_shown = live
    on, horde = live is not None, session.running()
    _visible(widgets["normal_live_box"], on)
    _visible(widgets["normal_locked"], on)
    _visible(widgets["normal_blocked"], horde and not on)
    _visible(widgets["normal_start_box"], not on and not horde)
    for option in normal_options.LOCKED:
        name = option.identifier
        widgets[f"setting:{name}"].SetIsEnabled(not on)
        for part in ("row", "description"):
            widgets[f"{part}:{name}"].SetRenderOpacity(t.OPACITY_DISABLED if on else 1.0)
    chosen = normal_options.read().level.name
    widgets[f"description:{normal_options.level.identifier}"].SetText(i18n.text(f"normal_level:{chosen}", language))
    widgets[f"heading:{KEY}"].SetText(i18n.text("normal_settings", language))
    widgets[f"group:{KEY}"].SetText(i18n.text("normal_lead", language))
    widgets["normal_locked"].SetText(i18n.text("normal_locked", language))
    widgets["normal_blocked"].SetText(i18n.text("normal_blocked", language))
    widgets["normal_start_label"].SetText(i18n.text("start", language))
    widgets["normal_stop_label"].SetText(i18n.text("stop", language))
    widgets["group:normal_live"].SetText("")
    widgets[f"heading:{HARDCORE}"].SetText(i18n.text("hardcore_settings", language))
    widgets[f"group:{HARDCORE}"].SetText(i18n.text("hardcore_lead", language))
    _visible(widgets["hardcore_progress_box"], normal_options.hardcore.value is True)
    if on:
        level = panel_choices.label(live.level, language, normal_options.level)
        widgets["heading:normal_live"].SetText(i18n.text("normal_live", language).format(level=level))
        widgets["normal_live_text"].SetText(i18n.text("normal_playing" if live.playing else "normal_waiting",
                                                      language))


def changed(form: Any) -> bool:
    """Whether the mode shown is no longer the mode as it stands: turned on or off, or found a game or left it while the
    game ran under the window."""
    return session.normal_live() != getattr(form, "normal_shown", None)


def start(form: Any, widgets: dict) -> str | bool:
    """START: the mode on; playing, it closes the window ("leave"); waiting or refused, said in the footer."""
    if not form.flush(widgets):
        form.notice = "start_busy"
        return True
    if not form.model.mod.is_enabled:
        form.notice = "start_off"
        return True
    if session.running():
        form.notice = REFUSALS["horde_running"]
        return True
    if form.model.save(((normal_options.on, True),)) is not True:
        form.notice = "start_busy"
        return True
    game_pause.release()
    outcome = session.start_normal(normal_options.read())
    report.note("normal_start_pressed", outcome=outcome)
    if outcome == "playing":
        return "leave"
    game_pause.hold()
    if outcome != "waiting":
        form.model.save(((normal_options.on, False),))
    form.notice = "normal_waiting_notice" if outcome == "waiting" else REFUSALS.get(outcome, "start_refused")
    return True


def stop(form: Any) -> bool:
    """STOP: the choice written off, then the mode off."""
    saved = form.model.save(((normal_options.on, False),))
    game_pause.release()
    outcome = session.stop_normal("stopped")
    game_pause.hold()
    report.note("normal_stop_pressed", outcome=outcome, saved=saved)
    form.notice = "ready" if saved is True else "normal_stop_unsaved"
    return True
