"""The RUN page (sketches 1 and 2 of esquisses_menu, validated by Kevin): the run's settings card, its caution about the
PC (decisions 54 and 60), its rows (level, speed, time limit, the killed coming back) and START across it; while a run
goes on, above it the run's card, its level, kills, deaths and time with STOP, and the settings locked under a line that
says to stop the run to change them (decision 51), the caution and START away. While the normal mode is on, the caution
and START give way to a line that says to stop it first (decision 80: one mode at a time). A « ? » beside START, and
beside STOP during a run, opens the help on how a run goes (panel_help.py).

START gives the game its pause back while the run starts, as BL4 Arena's LAUNCH does: every trial started a run in a
running game, never in a paused one; a run that starts closes the window without the mods list, the player going to
the fight. STOP gives the pause back while the run stops, then holds it again: the run's result shows over the window
(panel_result.py)."""

from typing import Any

from . import game_pause, options, panel_buttons as b, panel_figures as figures, panel_help as help_, panel_i18n as i18n
from . import panel_pages as p, panel_text as tx, panel_theme as t, panel_warning as warning, panel_widgets as w
from . import panel_words as words, report, session

# What a start refused says in the footer, by session.start's answer; any other answer is a refusal of the run itself.
REFUSALS = ("already_running", "normal_on", "in_vehicle", "no_character", "coop", "start_failed")


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    widgets["run_live_box"] = live = w.new("VerticalBox", body)
    w.column(body, live)
    rows = p.card(live, widgets, "run_live")
    line = w.new("HorizontalBox", rows)
    w.row(line, figures.build(line, widgets, "live"), fill=True, valign="Center")
    stop = b.button(line, widgets, "run_stop", "launch", template, "stop")
    w.row(line, w.sized(line, stop, width=t.STOP_WIDTH), valign="Center")
    w.row(line, help_.button(line, widgets, "live_help", template), padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, t.SPACE_2))
    rows = p.card(body, widgets, key)
    widgets["run_caution"] = warning.caution(rows, widgets, "run_caution_text")
    w.column(rows, widgets["run_caution"], padding=w.pad(t.SPACE_3, 0, t.SPACE_2))
    widgets["run_locked"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets["run_locked"], padding=w.pad(t.SPACE_2, 0))
    p.setting_rows(rows, group.children, widgets, template, expose_rows=True)
    widgets["run_blocked"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets["run_blocked"], padding=w.pad(t.SPACE_5, 0, t.SPACE_2))
    widgets["run_start_box"] = line = w.new("HorizontalBox", rows)
    w.row(line, b.button(line, widgets, "run_start", "launch", template, "primary"), fill=True, valign="Center")
    w.row(line, help_.button(line, widgets, "run_help", template), padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_5, 0, t.SPACE_2))
    return scroll


def paint(form: Any, widgets: dict, language: str) -> None:
    live = session.live()
    form.run_shown = live
    going, normal = live is not None, session.normal_on()
    _visible(widgets["run_live_box"], going)
    _visible(widgets["run_caution"], not going and not normal)
    _visible(widgets["run_locked"], going)
    _visible(widgets["run_blocked"], normal and not going)
    _visible(widgets["run_start_box"], not going and not normal)
    for option in options.RUN:
        name = option.identifier
        locked = going or option in options.SHELVED
        widgets[f"setting:{name}"].SetIsEnabled(not locked)
        for part in ("row", "description"):
            widgets[f"{part}:{name}"].SetRenderOpacity(t.OPACITY_DISABLED if locked else 1.0)
    widgets["heading:run"].SetText(i18n.text("run_settings", language))
    widgets["group:run"].SetText("")
    widgets["run_caution_text"].SetText(i18n.text("caution", language))
    widgets["run_locked"].SetText(i18n.text("locked", language))
    widgets["run_blocked"].SetText(i18n.text("run_blocked", language))
    widgets["run_start_label"].SetText(i18n.text("start", language))
    widgets["run_stop_label"].SetText(i18n.text("stop", language))
    widgets["group:run_live"].SetText("")
    if going:
        widgets["heading:run_live"].SetText(i18n.text("run_live", language).format(
            level=words.level(live.level, language)))
        figures.paint(widgets, "live", language, live.kills, live.deaths, live.played_s, live.limit_s)


def changed(form: Any) -> bool:
    """Whether the run shown is no longer the run as it stands: one ended, began, or counted more while the game ran
    under the window (a game it could not pause)."""
    return session.live() != getattr(form, "run_shown", None)


def start(form: Any, widgets: dict) -> str | bool:
    """START: the run started closes the window ("leave"); a refusal is said in the footer, the window kept."""
    if not form.flush(widgets):
        form.notice = "start_busy"
        return True
    if not form.model.mod.is_enabled:
        form.notice = "start_off"
        return True
    game_pause.release()
    outcome = session.start(options.read(form.model.language))
    report.note("start_pressed", outcome=outcome)
    if outcome == "started":
        return "leave"
    game_pause.hold()
    form.notice = f"start_{outcome}" if outcome in REFUSALS else "start_refused"
    return True


def stop(form: Any) -> bool:
    """STOP: the run stopped; its result shows next (panel_follows.poll_over)."""
    game_pause.release()
    outcome = session.stop("stopped")
    game_pause.hold()
    report.note("stop_pressed", outcome=outcome)
    form.notice = "ready"
    return True
