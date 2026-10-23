"""Companions' owner of the team (characters/companions/team.py): it starts the team with the companions chosen and
the settings read at that moment (tuning_given.py), stops it, and stops it when the team asks: at the main menu
(decision 61 of docs/renforts), or when another mod comes to lead the team (owners.py: It Follows, when both are on).
A companion taken away by a map change comes back by itself (team.py, decision 59). The companions' camps are kept for
the whole game session, as It Follows keeps its own (decision 59: one set of camps for every team). The bars' service
starts with the team (companions/bars.py), the bars shown while their setting says so.

Beside It Follows 1.0.10 or before, which runs a team of its own without joining the owners, no team starts
(outdated.py). Why none may start is said here once, for the window (blocked); the team's key gets the same refusal
from start_team, written in the log.
"""

from typing import Any

import mods_base

from . import outdated, report, settings, tuning_given
from .characters.companions import bars, main_menu, owners, team as companions_team

# The team while it is on, None while it is off; the companions' camps, kept from one team to the next.
_state: dict[str, Any] = {"team": None, "births": None}


def team_on() -> bool:
    return _state["team"] is not None


def blocked() -> str | None:
    """Why no team of Companions may start now, as the window's text that says it; None when one may: It Follows
    1.0.10 or before in the game (team_outdated), copies of the companions' code of two versions, so that no mod can
    be known to lead (team_mismatch, owners.py), or It Follows leading the team (team_elsewhere)."""
    if outdated.old_it_follows():
        return "team_outdated"
    if owners.leads() == owners.UNKNOWN:
        return "team_mismatch"
    return "team_elsewhere" if owners.elsewhere(companions_team.OWNER) else None


def start_team(names: list[str]) -> str:
    """The companions chosen, by their name (companions/kinds.py), called, then born and followed, each given the
    settings read now: "started", or why not: the team already on ("already_on"), It Follows 1.0.10 or before in the
    game ("it_follows_outdated"), the main menu showing ("main_menu": the team would stop at once), none chosen
    ("empty"), another mod leading the team or none known to ("elsewhere"). Without a hunter on foot they wait."""
    if _state["team"] is not None:
        return "already_on"
    if outdated.old_it_follows():
        report.note("team_refused", why="it_follows_outdated", module=outdated.OLD_TEAM)
        return "it_follows_outdated"
    if main_menu.showing(mods_base.get_pc()) is True:
        return "main_menu"
    if _state["births"] is None:
        _state["births"] = companions_team.new_births()
    team = companions_team.Team(births=_state["births"], end=lambda why: _team_ended(team, why))
    outcome = team.start(names, tuning_given.given())
    if outcome == "started":
        _state["team"] = team
        # Started whatever the bars' setting: it also names the hunter aimed at (decision 53), and reads the setting
        # at each publish.
        team.bars = bars.start(team.clock, lambda: settings.bars.value is True)
    return outcome


def _team_ended(team: Any, why: str) -> None:
    """A team asking to stop, stopped here, its owner, if it is still the one on."""
    if _state["team"] is team:
        stop_team(why)


def stop_team(reason: str = "stopped") -> str:
    """Ends the team: every follow ended, its companions taken out of the world, those on their way forgotten:
    "stopped", or "not_on". The team's stop removes its hook whatever fails in it (team.py), so that forgetting it
    here never leaves one running unowned."""
    team, _state["team"] = _state["team"], None
    if team is None:
        return "not_on"
    team.stop(reason)
    return "stopped"
