"""It Follows' pages wired into our windows' form (docs/RUN/outils/menu_window.py writes the calls): HORDE MODE (key
run), NORMAL MODE, HISTORY and OPTIONS drawn by their own modules, the welcome, the update notes, a run's result and
the « ? »'s help over the whole window, the RUNNING tag of each mode's button while it is on, the Hardcore's tag at the
top (panel_hardcore.py), the footer's sentence while nothing else is said, and the key that opens the window closing it
too (open_key.py).

The game stands still while the window is open (game_pause.py), except while START starts a mode or STOP stops it
(panel_run.py, panel_normal.py)."""

from typing import Any

from . import game_pause, open_key, panel_buttons as b, panel_history, panel_i18n as i18n, panel_options
from . import panel_hardcore, panel_help, panel_normal, panel_result, panel_run, panel_updates
from . import panel_text as tx, panel_theme as t, panel_welcome, panel_widgets as w, report, session, updates, welcome

# What poll answers when the window must close without the mods list (a mode that starts), and when it closes as its
# CLOSE button does (panel_form.py, control_window.py).
LEAVE, CLOSE = "leave", "close"
RUN, NORMAL, HISTORY, OPTIONS = "run", "normal", "history", "options"
PAGES = {RUN: panel_run.page, NORMAL: panel_normal.page, HISTORY: panel_history.page, OPTIONS: panel_options.page}
# Each mode's button tag: its widgets' name, and whether that mode is on.
TAGS = {RUN: ("nav_running", session.running), NORMAL: ("nav_normal_running", session.normal_on)}


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    if key == RUN:
        # Over the whole window, in its pop-up layer, which the view makes before its pages.
        panel_welcome.build(widgets, template)
        panel_updates.build(widgets, template)
        panel_result.build(widgets, template)
        panel_help.build(widgets, template)
    return PAGES[key](owner, group, key, widgets, template)


def nav_button(owner: Any, widgets: dict, key: str, template: Any) -> Any:
    """A page's button in the column; each mode's carries the RUNNING tag on its right while it is on (sketch 2)."""
    button = b.button(owner, widgets, f"nav:{key}", "nav", template, "nav_off")
    if key not in TAGS:
        return button
    name = TAGS[key][0]
    stack = w.new("Overlay", owner)
    w.layer(stack, button)
    tag = w.border(stack, t.COLOR_INK, w.pad(t.SPACE_1, t.SPACE_2))
    widgets[name] = tx.text(tag, "", "tag")
    tag.SetContent(widgets[name])
    widgets[f"{name}_tag"] = tag
    w.layer(stack, w.slant(tag), padding=w.pad(0, t.SPACE_4, 0, 0), halign="Right", valign="Center")
    return stack


def start(form: Any) -> None:
    """When the window's form is made: the welcome the first time it opens, else the notes of an update, else a run's
    result waiting; never two at once, the next waiting for the next opening (a result, as soon as nothing shows)."""
    from . import __version__

    form.run_shown = form.result = None
    form.update_notes, form.update_page = [], 0
    open_key.align()
    form.closer = open_key.closer()
    widgets = form.resolve()
    if welcome.due():
        panel_welcome.open_first(form, widgets)
        return
    notes = updates.due(__version__)
    if notes:
        panel_updates.open_first(form, widgets, notes)
    else:
        panel_result.open_waiting(form, widgets)


def _go(form: Any, widgets: dict, key: str) -> None:
    """The window turned to page key, as its column's buttons turn it (panel_form.py)."""
    if form.flush(widgets) and form.model.change_page(key):
        form.page = form.model.pages.index(key)
        widgets["pages"].SetActiveWidgetIndex(form.page)
    form.refresh_labels(widgets)


def poll_over(form: Any, widgets: dict) -> bool:
    """What lies over the whole window, read alone while it shows: the welcome, the update notes, then a run's result,
    shown as soon as one waits and nothing else is open. Whether one of them shows. First at each poll, whatever shows:
    the pause looked at once a second (game_pause.watch)."""
    game_pause.watch()
    if form.popup in (panel_welcome.KEY, panel_updates.KEY, panel_result.KEY) and form.closer is not None:
        form.closer.released(True)  # the opening key heard by no one, so that it never closes the window afterwards
    if panel_welcome.poll(form, widgets) or panel_updates.poll(form, widgets):
        return True
    shown = panel_result.poll(form, widgets)
    if shown == "history":
        _go(form, widgets, HISTORY)
    if shown:
        return True
    return form.popup is None and panel_result.open_waiting(form, widgets)


def _follow_key(form: Any) -> None:
    """The SDK's keybind and the closing watch given the key just chosen."""
    if open_key.align():
        form.closer = open_key.closer()


def poll(form: Any, widgets: dict) -> str | bool:
    """The page's own buttons and the key's field; LEAVE or CLOSE when the window must close, else whether something
    was handled."""
    _follow_key(form)
    if form.closer is not None and form.closer.released(panel_options.selecting(widgets)):
        report.note("open_key_closes", key=open_key.key())
        return CLOSE if form.flush(widgets) else True
    if form.take(widgets["run_start"]):
        outcome = panel_run.start(form, widgets)
        form.refresh_labels(widgets)
        return outcome
    if form.take(widgets["run_stop"]):
        panel_run.stop(form)
        form.refresh_labels(widgets)
        return True
    if form.take(widgets["normal_start"]):
        outcome = panel_normal.start(form, widgets)
        form.refresh_labels(widgets)
        return outcome
    if form.take(widgets["normal_stop"]):
        panel_normal.stop(form)
        form.refresh_labels(widgets)
        return True
    if panel_help.poll(form, widgets):
        return True
    if panel_options.poll_key(form, widgets):
        _follow_key(form)
        form.refresh_labels(widgets)
        return True
    if panel_options.look_changed(form) or panel_run.changed(form) or panel_normal.changed(form):
        form.refresh_labels(widgets)
        return True
    return False


def selecting(form: Any) -> bool:
    return panel_options.selecting(form.resolve())


def paint(form: Any, widgets: dict, language: str) -> None:
    panel_run.paint(form, widgets, language)
    panel_normal.paint(form, widgets, language)
    panel_history.paint(widgets, language)
    panel_options.paint(form, widgets, language)
    panel_welcome.paint(widgets, language)
    panel_updates.paint(form, widgets, language)
    panel_result.paint(form, widgets, language)
    panel_hardcore.paint(widgets, language)
    for name, on in TAGS.values():
        widgets[name].SetText(i18n.text("running_tag", language))
        widgets[f"{name}_tag"].SetVisibility(w.enum("ESlateVisibility", "HitTestInvisible" if on() else "Collapsed"))


def notice(form: Any, language: str) -> str:
    """The footer's sentence: the page's own while the window has nothing else to say. On a mode's page, the pause
    while either mode is on: the other's START is away then, and READY would ask to press it (trial 20)."""
    if form.notice != "ready":
        return i18n.text(form.notice, language)
    key = form.model.pages[form.page]
    if key in TAGS:
        return i18n.text("paused_run" if any(on() for _, on in TAGS.values()) else f"ready_{key}", language)
    return i18n.text("ready_history" if key == HISTORY else "ready_options", language)
