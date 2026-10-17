"""The DUEL page, the window's only one: how a duel goes, then START DUEL; while a duel goes on, its score and STOP DUEL
instead (Kevin, 17 October 2026: no end, the host stops it in the menu). A refusal to start is said in the footer with
its real cause and what to do, the game left as it was. START closes the window without the mods list, the players
going to the fight, as It Follows' START does (its control_window passages, docs/duel/outils/menu_window.py).

The page holds no setting: only these two buttons, read at each poll of the window (poll), and the duel as duel.py
holds it. docs/duel/outils/menu_window.py writes the calls into the generated window."""

from typing import Any

from . import duel, menu, panel_buttons as b, panel_i18n as i18n, panel_pages as p, panel_text as tx
from . import panel_theme as t, panel_widgets as w, report

KEY = menu.duel.identifier.removesuffix("_menu")
# What poll answers when the window must close without the mods list (control_window.py).
LEAVE = "leave"


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    widgets["duel_how"] = tx.text(rows, "", "body", wrap=True)
    w.column(rows, widgets["duel_how"], padding=w.pad(t.SPACE_3, 0, t.SPACE_2))
    widgets["duel_live"] = live = w.new("VerticalBox", rows)
    widgets["duel_score"] = tx.text(live, "", "hero", center=True)
    w.column(live, widgets["duel_score"], padding=w.pad(t.SPACE_5, 0, t.SPACE_3), halign="Center")
    w.column(live, b.button(live, widgets, "duel_stop", "action", template, "secondary"), halign="Center")
    w.column(rows, live)
    widgets["duel_start_box"] = start_box = w.new("VerticalBox", rows)
    w.column(start_box, b.button(start_box, widgets, "duel_start", "action", template, "primary"), halign="Left")
    w.column(rows, start_box, padding=w.pad(t.SPACE_5, 0, t.SPACE_2))
    return scroll


def paint(form: Any, widgets: dict, language: str) -> None:
    shown = duel.live()
    form.duel_shown = shown
    going = shown is not None
    _visible(widgets["duel_live"], going)
    _visible(widgets["duel_start_box"], not going)
    widgets["duel_how"].SetText(i18n.text("duel_how", language))
    widgets["duel_start_label"].SetText(i18n.text("start", language))
    widgets["duel_stop_label"].SetText(i18n.text("stop", language))
    if going:
        widgets["duel_score"].SetText(f"{shown.host_name}  {shown.host} - {shown.guest}  {shown.guest_name}")


def notice(form: Any, language: str) -> str:
    """The footer's sentence: the page's own while the window has nothing else to say."""
    if form.notice != "ready":
        return i18n.text(form.notice, language)
    return i18n.text("ready_on" if duel.live() is not None else "ready_duel", language)


def start(form: Any) -> str | bool:
    if not form.model.mod.is_enabled:
        form.notice = "start_off"
        return True
    outcome = duel.start(form.model.language)
    report.note("start pressed", outcome=outcome)
    if outcome == "started":
        form.notice = "ready"
        return LEAVE
    form.notice = f"start_{outcome}" if outcome in duel.REFUSALS else "start_refused"
    return True


def poll(form: Any, widgets: dict) -> str | bool:
    """The page's two buttons, and the score followed while the window is open: LEAVE when the window must close, True
    after something was handled, False otherwise."""
    if form.take(widgets["duel_start"]):
        outcome = start(form)
        form.refresh_labels(widgets)
        return outcome
    if form.take(widgets["duel_stop"]):
        report.note("stop pressed", outcome=duel.stop("stopped"))
        form.notice = "ready"
        form.refresh_labels(widgets)
        return True
    if duel.live() != getattr(form, "duel_shown", None):
        form.refresh_labels(widgets)
        return True
    return False
