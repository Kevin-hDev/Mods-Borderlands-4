"""The one owner of the players' teams during a duel, every player but the host, who is never changed: which team of
the game each duel team gets, handing it, giving each his own back while a round is over and when the duel ends, and
reading each back. Nothing else in the mod calls SetTeam.

Friendly fire comes from teams, the host's game alone deciding (trial 1, verified in game): two players hurt each other
only when their teams of the game have different collision channels (OTHER_TEAMS). The host's duel team keeps
Team_Player, the players' own: its members are friends, as in any co-op game. Each other duel team gets its own team of
the game, shared by its members, who do not hurt each other. Team_Hostile, the first, is hostile to every team of the
game's table: the enemies around attack its players instead of siding with them (trial 8, docs/duel/enquetes/
2026-10-17-equipe-hostile.md, verified in game).

Each team is built by its name with the type of SetTeam's own Team parameter, and taken as built (trials 2 to 8). A
player's own team is read from the game before the first hand, never assumed: it is the one given back."""

import re
from collections.abc import Iterable
from itertools import combinations
from typing import Any

import unrealsdk
from unrealsdk.unreal import WeakPointer

from . import players, report

LIBRARY = "GbxTeamFunctionLibrary"
SETTER, PARAMETER = "SetTeam", "Team"
DUEL_TEAM = "Team_Hostile"
PLAYERS_TEAM = "Team_Player"
# The game's teams of the duel teams other than the host's, given in their numbers' order. Two players hurt each other
# only when their teams have different collision channels in the game's team table, whatever attitude the game reads:
# two players both in Team_Hostile do not. Team_Player is Four, Team_Hostile none, Team_Bandit Two, Team_Order Three;
# the six pairs checked in game (trials 1 to 1e, docs/duel/enquetes/2026-10-17-equipes-du-jeu.md). Team_Hostile comes
# first: it gives its player no allies among the enemies around, and a duel of two teams needs no other.
OTHER_TEAMS = (DUEL_TEAM, "Team_Bandit", "Team_Order")
# The bandits or the Order's soldiers around side with the players given Team_Bandit or Team_Order: from this many duel
# teams on, the host's counted, a team gets them (teams_allies, the TEAMS page's footer).
ALLIES_FROM = 2 + OTHER_TEAMS.index("Team_Bandit")
NAMED = re.compile(r"'(Team_[A-Za-z0-9_]+)'")


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


def team_name(team: Any) -> str | None:
    """The team's name as the game shows its handle, "FGameDataHandle(15, 'Team_Player', None)"; None for anything
    else."""
    found = NAMED.search(report.shown(team)) if team is not None else None
    return found.group(1) if found else None


def plan(numbers: Iterable[int], host_team: int) -> dict[int, str]:
    """For each duel team with players, by its number, the game's team its players get: the host's keeps the players'
    own, the others take OTHER_TEAMS in their numbers' order. More teams than that raise ValueError."""
    others = iter(OTHER_TEAMS)
    given: dict[int, str] = {}
    for team in sorted(numbers):
        if team == host_team:
            given[team] = PLAYERS_TEAM
            continue
        name = next(others, None)
        if name is None:
            raise ValueError("more duel teams than the game's teams set apart for them")
        given[team] = name
    return given


class Member:
    """A player of the duel other than the host: his character held weakly, his number J, the team he had before the
    duel and the duel's; each hand and give-back read back, never assumed."""

    def __init__(self, found: Any, pawn: Any, number: int, own: Any, duel: Any) -> None:
        self.library, self.own, self.duel, self.number = found, own, duel, number
        self.own_name, self.duel_name = team_name(own), team_name(duel)
        self.pointer, self.label = WeakPointer(pawn), players.label(pawn)

    @property
    def name(self) -> str:
        return report.player(self.number)

    def pawn(self) -> Any:
        return self.pointer()

    def team(self) -> Any:
        """His team as the game reads it now, None when it cannot be read."""
        pawn = self.pawn()
        if pawn is None:
            return None
        try:
            return self.library.GetTeam(pawn)
        except Exception:
            return None

    def _set(self, team: Any, name: str | None) -> bool:
        pawn = self.pawn()
        if pawn is None:
            report.note("character gone, team left", player=self.name)
            return False
        done, _nothing = report.called(f"SetTeam({self.name} {self.label}, {name})",
                                       lambda: self.library.SetTeam(pawn, team))
        return done

    def holds_duel_team(self) -> bool:
        return team_name(self.team()) == self.duel_name

    def hand(self) -> bool:
        """The duel's team handed and read back: whether he holds it."""
        if not self._set(self.duel, self.duel_name):
            return False
        now = self.team()
        report.note("team handed", player=self.name, now=report.shown(now))
        return team_name(now) == self.duel_name

    def give_back(self) -> bool:
        """His own team handed and read back: whether he holds it. A SetTeam the game takes without applying it reads
        as a refusal, so that the give-back is tried again."""
        if not self._set(self.own, self.own_name):
            return False
        now = self.team()
        report.note("team given back", player=self.name, now=report.shown(now))
        return team_name(now) == self.own_name


def take(pawn: Any, number: int, duel_name: str) -> Member | None:
    """The player read before any change: his own team and the duel's, None when either cannot be had (nothing is
    changed then)."""
    done, found = report.called(f"find_class({LIBRARY})", library)
    if not done:
        return None
    name = report.player(number)
    done, own = report.called(f"GetTeam({name})", lambda: found.GetTeam(pawn))
    if not done or own is None:
        return None
    report.note("own team", player=name, team=report.shown(own))
    # Left in a duel's team by an earlier duel whose give-back the game refused: the players' team is his own.
    if team_name(own) in OTHER_TEAMS:
        own = built(PLAYERS_TEAM)
        report.note("own team was the duel's", player=name, team=report.shown(own))
        if own is None:
            return None
    duel = built(duel_name)
    return Member(found, pawn, number, own, duel) if duel is not None else None


def _attitude(found: Any, one: Any, other: Any) -> str:
    if one is None or other is None:
        return "no character"
    try:
        return report.shown(found.GetAttitudeTowards(one, other))
    except Exception as error:
        return f"unreadable {type(error).__name__}"


def attitudes(fighters: list[tuple[int, Any]]) -> None:
    """How the game sees each pair of players, both ways (0 friendly, 2 hostile). Damage between players follows their
    teams' collision channels, not this (OTHER_TEAMS): two teammates in Team_Hostile read 2 and do not hurt each other.
    The line still tells at once a team the game did not take."""
    done, found = report.called(f"find_class({LIBRARY})", library)
    if not done:
        return
    for (one, first), (other, second) in combinations(fighters, 2):
        report.note("attitudes", a=report.player(one), b=report.player(other), a_to_b=_attitude(found, first, second),
                    b_to_a=_attitude(found, second, first))
