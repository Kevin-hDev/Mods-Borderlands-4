"""The players of the session as the host sees them, and the duel team the host gives each on the TEAMS page (Kevin,
17 October 2026, docs/duel/spec-equipes.md): four teams at most, each player alone in his own at first, in the smallest
number free. Kept in memory for the session only: the players change from one game to the next, and nothing is
written on the disk.

A player is known by his PlayerState, held weakly. After a travel the game may give him a new one: a newcomer bearing
the name of a player gone at the same read takes his seat back. A seat's number, J1 to J4, the smallest free when the
player is first seen, names him in the log; his player name stays in memory, for the window and the screen only."""

from dataclasses import dataclass
from itertools import islice
from typing import Any, Iterable

from unrealsdk.unreal import WeakPointer

from . import players, report

TEAMS = (1, 2, 3, 4)
# A game of Borderlands 4 holds 4 players: past them, a player gets no seat and no team.
MAX_SEATS = 4
# Where the window stands: the host's game, a guest's (only the host arranges the teams), or none read yet.
HOST, GUEST, NOWHERE = "host", "guest", "nowhere"


@dataclass(eq=False)
class Seat:
    number: int
    team: int
    host: bool
    name: str
    pointer: Any

    def state(self) -> Any:
        return self.pointer()

    def holds(self, state: Any) -> bool:
        mine = self.state()
        return mine is not None and mine == state


def _free(taken: Iterable[int]) -> int:
    used = set(taken)
    return next((number for number in TEAMS if number not in used), TEAMS[0])


class Roster:
    def __init__(self) -> None:
        self.seats: list[Seat] = []
        self.where = NOWHERE

    def seat_of(self, state: Any) -> Seat | None:
        return next((seat for seat in self.seats if seat.holds(state)), None)

    def sync(self, found: list[players.Player]) -> None:
        """The seats made those of found's players, read in the host's game: a player gone loses his seat, a new one
        gets the smallest number and the smallest team free."""
        present = list(islice(found, MAX_SEATS))
        names = [players.player_name(player.state, "") for player in present]
        held: list[Seat | None] = [self.seat_of(player.state) for player in present]
        gone = [seat for seat in self.seats if not any(seat is kept for kept in held)]
        for index, seat in enumerate(held):
            twin = None if seat is not None else next(
                (old for old in gone if old.name and old.name == names[index]), None)
            if twin is not None:
                gone.remove(twin)
                twin.pointer = WeakPointer(present[index].state)
                held[index] = twin
        self.seats = [seat for seat in self.seats if not any(seat is old for old in gone)]
        for index, player in enumerate(present):
            seat = held[index]
            if seat is None:
                seat = Seat(_free(seat.number for seat in self.seats), _free(seat.team for seat in self.seats),
                            player.host, names[index], WeakPointer(player.state))
                self.seats.append(seat)
            seat.host, seat.name = player.host, names[index] or seat.name
        self.seats.sort(key=lambda seat: seat.number)
        self.where = HOST

    def set_team(self, number: int, team: int) -> bool:
        """The player of this number put in this team: whether it changed."""
        seat = next((seat for seat in self.seats if seat.number == number), None)
        if seat is None or team not in TEAMS or seat.team == team:
            return False
        seat.team = team
        return True

    def each_alone(self) -> None:
        """Every player alone in his team: the host in the first, the others after him in the order of their
        numbers."""
        for seat, team in zip(sorted(self.seats, key=lambda seat: (not seat.host, seat.number)), TEAMS):
            seat.team = team

    def groups(self) -> dict[int, list[Seat]]:
        """The teams with players, by number, each with its seats by number."""
        found: dict[int, list[Seat]] = {}
        for seat in sorted(self.seats, key=lambda seat: (seat.team, seat.number)):
            found.setdefault(seat.team, []).append(seat)
        return found


ROSTER = Roster()


def refresh() -> None:
    """The roster read from the game: synced in the host's game once he has a character, marked a guest's game
    otherwise, left as it is without a game, the next read setting it right."""
    world = players.world()
    if world is None:
        return
    try:
        found = players.everyone(world)
    except Exception as error:
        report.error_once(f"roster:{type(error).__name__}", f"the players could not be read ({type(error).__name__})")
        return
    if found is None:
        ROSTER.where = GUEST
    elif found and found[0].host and found[0].pawn is not None:
        ROSTER.sync(found)
