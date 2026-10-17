"""The one owner of the guest's team during a duel: it hands him the duel's team, gives him his own back while a player
is KO, and gives it back for good when the duel ends. Nothing else in the mod calls SetTeam.

Friendly fire comes from teams: the guest in a team hostile to the players' makes host and guest hurt each other both
ways, the host's game alone deciding (trial 1, verified in game). The duel's team is Team_Hostile, hostile to every
team in the game's table: the enemies around attack both players instead of siding with the guest, as Team_Bandit's
bandits did (trial 8, docs/duel/enquetes/2026-10-17-equipe-hostile.md, verified in game). It is built by its name, with
the type of SetTeam's own Team parameter, and taken as built (trials 2 to 8). The guest's own team is read from the
game before the first hand, never assumed: it is the one given back.
"""

from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer

from . import players, report

LIBRARY = "GbxTeamFunctionLibrary"
SETTER, PARAMETER = "SetTeam", "Team"
DUEL_TEAM = "Team_Hostile"
PLAYERS_TEAM = "Team_Player"
HOSTILE = 2


def library() -> Any:
    return unrealsdk.find_class(LIBRARY).ClassDefaultObject


def built(name: str) -> Any:
    """The team's handle, built by its name with the type SetTeam's own parameter takes; None when it cannot be."""
    done, kind = report.called(f"type of {SETTER}.{PARAMETER}", lambda: int(
        unrealsdk.find_class(LIBRARY)._find(SETTER)._find(PARAMETER).TypeHandle))
    if not done:
        return None
    done, team = report.called(f"FGameDataHandle({kind}, {name})",
                               lambda: unrealsdk.unreal.FGameDataHandle(kind, name))
    return team if done else None


def holds_duel_team(team: Any) -> bool:
    return f"'{DUEL_TEAM}'" in report.shown(team)


class Guest:
    """The guest in a duel: his character held weakly, the team he had before it, the duel's team."""

    def __init__(self, teams: Any, pawn: Any, own: Any, duel: Any) -> None:
        self.teams, self.own, self.duel = teams, own, duel
        self.pointer, self.label = WeakPointer(pawn), players.label(pawn)

    def pawn(self) -> Any:
        return self.pointer()

    def team(self) -> Any:
        """His team as the game reads it now, None when it cannot be read."""
        pawn = self.pawn()
        if pawn is None:
            return None
        try:
            return self.teams.GetTeam(pawn)
        except Exception:
            return None

    def _set(self, team: Any) -> bool:
        pawn = self.pawn()
        if pawn is None:
            report.note("character gone, team left", character=self.label)
            return False
        done, _nothing = report.called(f"SetTeam({self.label}, {report.shown(team)})",
                                       lambda: self.teams.SetTeam(pawn, team))
        return done

    def hand(self) -> bool:
        """The duel's team handed and read back: whether he holds it."""
        if not self._set(self.duel):
            return False
        now = self.team()
        report.note("team handed", character=self.label, now=report.shown(now))
        return holds_duel_team(now)

    def give_back(self) -> bool:
        """His own team handed and read back: whether he left the duel's team. A SetTeam the game takes without
        applying it reads as a refusal, so that the give-back is tried again."""
        if not self._set(self.own):
            return False
        now = self.team()
        report.note("team given back", character=self.label, now=report.shown(now))
        return not holds_duel_team(now)

    def hostile(self, host: Any) -> bool | None:
        """Whether host and guest see each other hostile both ways; None when it cannot be read."""
        pawn = self.pawn()
        if pawn is None or host is None:
            return None
        try:
            both = (self.teams.GetAttitudeTowards(host, pawn), self.teams.GetAttitudeTowards(pawn, host))
        except Exception:
            return None
        report.note("attitudes", character=self.label, host_to_guest=report.shown(both[0]),
                    guest_to_host=report.shown(both[1]))
        return all(report.shown(value) == str(HOSTILE) for value in both)


def take(pawn: Any) -> Guest | None:
    """The guest read before any change: his own team and the duel's, None when either cannot be had (nothing is
    changed then)."""
    done, teams = report.called(f"find_class({LIBRARY})", library)
    if not done:
        return None
    label = players.label(pawn)
    done, own = report.called(f"GetTeam({label})", lambda: teams.GetTeam(pawn))
    if not done or own is None:
        return None
    report.note("own team", character=label, team=report.shown(own))
    # Left in the duel's team by an earlier duel whose give-back the game refused: the players' team is his own.
    if holds_duel_team(own):
        own = built(PLAYERS_TEAM)
        report.note("own team was the duel's", character=label, team=report.shown(own))
        if own is None:
            return None
    duel = built(DUEL_TEAM)
    return Guest(teams, pawn, own, duel) if duel is not None else None
