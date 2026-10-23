"""The VAULT HUNTERS and ALLIES pages' clicks (panel_cards.py): a card's name adding one more to the team, its « − »
taking one away, a hunter's outfit chosen, each written at once through the window's settings transaction
(team_choices.py), so that the team is kept from one launch to the next; a ninth refused, said in the footer
(spec-compagnons.md: « un 9e ajout est refusé avec un message »). While the team is on, or none may start, the cards
are greyed and take no click (panel_cards.py); a click that comes anyway changes nothing and says why. The launch
button starts the team with the choices kept and the settings as they are, and closes the window, the player going
to them; while the team is on, it stops it and the window stays. Every button is read at each poll, so that none
keeps a click for later."""

from typing import Any

from . import panel_cards as cards, report, session, settings, team_choices as choices
from .characters.companions import kinds

# What closes the window without the mods list (panel_team.LEAVE).
LEAVE = "leave"
# A launch refused: the window's notice for each answer of session.start_team; "elsewhere" says why no mod lets
# this one lead (session.blocked); an answer none of these, said as such, never as « none chosen ».
NOTICES = {"already_on": "team_already_on", "main_menu": "team_main_menu", "elsewhere": "team_elsewhere",
           "it_follows_outdated": "team_outdated", "empty": "team_empty"}


def _save(form: Any, widgets: dict, option: Any, value: Any) -> None:
    saved = form.flush(widgets) and form.model.save(((option, value),))
    form.notice = "saved" if saved else "ready" if saved is None else form.failure_notice()


def _card(form: Any, widgets: dict, name: str, clicked: str) -> None:
    """One button of that companion's card, by its name (panel_cards.buttons)."""
    pieces = clicked.removeprefix("mate_").split(":")
    kind, value = pieces[0], pieces[2] if len(pieces) > 2 else ""
    if kind == "add":
        team = choices.added(name)
        if team is None:
            form.notice = "team_full"
        else:
            _save(form, widgets, settings.team, team)
    elif kind == "minus":
        _save(form, widgets, settings.team, choices.removed(name))
    else:
        _save(form, widgets, settings.outfits, choices.with_outfit(name, value))
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
        outcome = session.start_team(names)
        report.note("companions_launch_pressed", outcome=outcome, companions=names)
        if outcome == "started":
            return LEAVE
        form.notice = (session.blocked() or "team_elsewhere") if outcome == "elsewhere" else NOTICES.get(
            outcome, "team_not_started")
    return True


def poll(form: Any, widgets: dict) -> str | bool:
    """Whether a button of the pages was clicked and handled; LEAVE when the team started."""
    clicked = {kind.name: [button for button in cards.buttons(kind.name) if form.take(widgets[button])]
               for kind in kinds.ALL}
    launch = [key for key in cards.PAGES if form.take(widgets[f"team_launch:{key}"])]
    picked = [(name, pressed[0]) for name, pressed in clicked.items() if pressed]
    if not (picked or launch):
        return False
    if launch:
        outcome = _launch(form, widgets)
        if outcome == LEAVE:
            return LEAVE
    elif session.team_on() or session.blocked() is not None:
        form.notice = "cards_locked" if session.team_on() else session.blocked()
    else:
        _card(form, widgets, *picked[0])
    form.refresh_labels(widgets)
    return True
