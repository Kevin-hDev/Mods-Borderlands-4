"""The COMPANIONS page's clicks (panel_companions.py): a tab opened; a card's name adding one more to the team, its
« − » taking one away, its shield switched, a speed chosen, each written at once through the window's settings
transaction (companion_choices.py), so that the team is kept from one launch to the next; the outfit of the hunter
the player plays chosen; a ninth refused, said in
the footer (spec-compagnons.md: « un 9e ajout est refusé avec un message »). While the team is on, the cards are
locked: a click on one says so. The launch button starts the team with the choices kept and closes the window, as
START does, the player going to them; while the team is on, it stops it and the window stays. Every button is read
at each poll, so that none keeps a click for later."""

from typing import Any

from . import companion_choices as choices, panel_companions as cards, report, session
from .characters.companions import kinds

# What closes the window without the mods list (panel_follows.LEAVE).
LEAVE = "leave"
# A launch refused: the window's notice for each answer of session.start_team; any other, as none chosen. It
# Follows leads the team before any mod (owners.py): refused as elsewhere, no mod can be known to lead, its copy of
# the characters' package and another mod's being of two versions.
NOTICES = {"already_on": "team_already_on", "main_menu": "team_main_menu", "elsewhere": "team_mismatch"}


def _save(form: Any, widgets: dict, option: Any, value: Any) -> None:
    saved = form.flush(widgets) and form.model.save(((option, value),))
    form.notice = "saved" if saved else "ready" if saved is None else form.failure_notice()


def _card(form: Any, widgets: dict, name: str, clicked: str) -> None:
    """One button of that companion's card, by its name (panel_companions.buttons)."""
    pieces = clicked.removeprefix("mate_").split(":")
    kind, value = pieces[0], pieces[2] if len(pieces) > 2 else ""
    if kind == "add":
        team = choices.added(name)
        if team is None:
            form.notice = "team_full"
        else:
            _save(form, widgets, choices.team, team)
    elif kind == "minus":
        _save(form, widgets, choices.team, choices.removed(name))
    elif kind == "shield":
        _save(form, widgets, choices.chosen, choices.changed(name, shielded=not choices.choice(name).shielded))
    elif kind == "speed":
        _save(form, widgets, choices.chosen, choices.changed(name, speed=value))
    else:
        _save(form, widgets, choices.chosen, choices.changed(name, outfit=value))
    report.note("companions_card", companion=name, clicked=kind if not value else f"{kind}:{value}",
                notice=form.notice)


def _launch(form: Any, widgets: dict) -> str | bool:
    if session.team_on():
        outcome = session.stop_team()
        form.notice = "team_stopped"
        report.note("companions_stop_pressed", outcome=outcome)
        return True
    names = choices.names()
    if not form.flush(widgets):
        form.notice = "team_busy"
    elif not form.model.mod.is_enabled:
        form.notice = "team_off"
    elif not names:
        form.notice = "team_empty"
    else:
        outcome = session.start_team(names, choices.team_choices())
        report.note("companions_launch_pressed", outcome=outcome, companions=names)
        if outcome == "started":
            return LEAVE
        form.notice = NOTICES.get(outcome, "team_empty")
    return True


def poll(form: Any, widgets: dict) -> str | bool:
    """Whether a button of the page was clicked and handled; LEAVE when the team started."""
    tabs = [tab for tab in cards.TABS if form.take(widgets[f"companions_tab:{tab}"])]
    clicked = {kind.name: [button for button in cards.buttons(kind.name) if form.take(widgets[button])]
               for kind in kinds.ALL}
    launch = form.take(widgets["companions_launch"])
    picked = [(name, pressed[0]) for name, pressed in clicked.items() if pressed]
    if not (tabs or picked or launch):
        return False
    if tabs:
        form.model.companions_tab = tabs[0]
    elif launch:
        outcome = _launch(form, widgets)
        if outcome == LEAVE:
            return LEAVE
    elif session.team_on():
        form.notice = "companions_locked"
    else:
        _card(form, widgets, *picked[0])
    form.refresh_labels(widgets)
    return True
