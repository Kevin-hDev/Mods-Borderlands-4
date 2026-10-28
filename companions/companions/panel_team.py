"""Companions' pages wired into our windows' form (docs/renforts/outils/menu_window.py writes the calls): VAULT HUNTERS
and ALLIES drawn by panel_cards.py, SETTINGS by panel_settings.py; their clicks and the two keys' fields read at each
poll; the footer's sentence while nothing else is said; and the key that opens the window closing it too
(open_key.py).

The game stands still while the window is open (game_pause.py, held by the window's start, given back at its
closing); the window looks once a poll whether it still does (game_pause.watch)."""

from typing import Any

from . import game_pause, open_key, panel_cards, panel_cards_poll, panel_i18n as i18n, panel_keys
from . import panel_settings, panel_values, report, session, team_choices, team_key
from .characters.companions import bars

# What poll answers when the window must close without the mods list (a team that starts), and when it closes as its
# CLOSE button does (panel_form.py, control_window.py).
LEAVE, CLOSE = panel_cards_poll.LEAVE, "close"


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    build = panel_settings.page if key == panel_settings.KEY else panel_cards.page
    return build(owner, group, key, widgets, template)


def start(form: Any) -> None:
    """When the window's form is made: the cards' state, whether the bars' package is in the game, the keys given to
    the SDK's keybinds and the closing watch."""
    panel_cards.reset(form)
    form.bars_offered = bars.installed()
    open_key.align()
    team_key.align()
    form.closer = open_key.closer()


def _follow_key(form: Any) -> None:
    """The SDK's keybinds and the closing watch given the keys just chosen."""
    team_key.align()
    if open_key.align():
        form.closer = open_key.closer()


def poll(form: Any, widgets: dict) -> str | bool:
    """The pages' own buttons and the keys' fields; LEAVE or CLOSE when the window must close, else whether something
    was handled."""
    game_pause.watch()
    _follow_key(form)
    if form.closer is not None and form.closer.released(panel_keys.selecting(widgets)):
        report.note("open_key_closes", key=open_key.key())
        return CLOSE if form.flush(widgets) else True
    polled = panel_cards_poll.poll(form, widgets)
    if polled:
        return polled
    if panel_keys.poll(form, widgets):
        _follow_key(form)
        form.refresh_labels(widgets)
        return True
    if panel_cards.changed(form):
        form.refresh_labels(widgets)
        return True
    return False


def selecting(form: Any) -> bool:
    return panel_keys.selecting(form.resolve())


def paint(form: Any, widgets: dict, language: str) -> None:
    panel_values.use(language)
    panel_cards.paint(form, widgets, language)
    panel_settings.paint(form, widgets, language)


def notice(form: Any, language: str) -> str:
    """The footer's sentence: the page's own while the window has nothing else to say. Why no team may start, on
    every page, before anything else (session.blocked); on a card page, how to change the team while it is on, or
    that Companions is disabled: never an invitation to launch what cannot be."""
    if form.notice != "ready":
        said = i18n.text(form.notice, language)
        return said.format(most=team_choices.MOST) if form.notice == "team_full" else said
    on, why = session.team_on(), session.blocked()
    if why is not None and not on:
        return i18n.text(why, language)
    if form.model.pages[form.page] == panel_settings.KEY:
        return i18n.text("ready_settings", language)
    if on:
        return i18n.text("team_on_notice", language)
    return i18n.text("ready_cards" if form.model.mod.is_enabled else "team_off", language)
