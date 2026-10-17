"""Who would fight a duel the host starts now, read from the game before anything is changed, or why no duel can
start: each refusal has its sentence in the window's texts (start_<refusal>), saying its real cause, that the game is
not changed, and what to do."""

from typing import Any, NamedTuple

from . import players, report, roster


class Lineup(NamedTuple):
    found: list[players.Player]  # the host first
    seats: list[roster.Seat]  # each player's, in found's order
    sizes: dict[int, int]  # each duel team with players, and how many


def _down(pawn: Any) -> bool:
    """Whether the game shows the player down; unreadable reads as not down, the duel's beat asking again."""
    try:
        return pawn.InDownState() is True
    except Exception:
        return False


def read(world: Any) -> Lineup | str:
    """The players and their teams, or the refusal."""
    try:
        found = None if world is None else players.everyone(world)
    except Exception as error:
        report.note("players unreadable", error=type(error).__name__)
        return "no_character"
    if world is not None and found is None:
        return "not_host"
    if not found or not found[0].host or found[0].pawn is None:
        return "no_character"
    if len(found) < 2:
        return "no_guest"
    if any(player.pawn is None for player in found):
        return "player_away"
    if not all(player.on_foot for player in found):
        return "in_vehicle"
    roster.ROSTER.sync(found)
    seats = [roster.ROSTER.seat_of(player.state) for player in found]
    if any(seat is None for seat in seats):
        report.note("player without a seat", players=len(found))
        return "team_refused"
    sizes: dict[int, int] = {}
    for seat in seats:
        sizes[seat.team] = sizes.get(seat.team, 0) + 1
    if len(sizes) < 2:
        return "one_team"
    # Down before the duel, by an enemy or a fall: seen at the first step, it would count as the duel's round.
    if any(_down(player.pawn) for player in found):
        return "player_down"
    return Lineup(found, seats, sizes)
