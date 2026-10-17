"""The players of the session (roster.py): the host J1 in team 1, each newcomer the smallest number and team free; a
team chosen, refused for a seat or a team that does not exist; a player gone losing his seat, the others keeping
theirs; a player back after a travel, under a new PlayerState and the same name, taking his seat back; EACH FOR
THEMSELVES; four seats at most; the game read by refresh in the host's game, marked a guest's otherwise; the names
kept in memory, never in the log."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import game_fixture  # noqa: E402

game = game_fixture.install(state)

from coop_duel import players, roster  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def seats(held: roster.Roster) -> list[tuple[int, int, bool, str]]:
    return [(seat.number, seat.team, seat.host, seat.name) for seat in held.seats]


Character = game_fixture.Character
host = Character("OakCharacter_1", "Kevin", local=True)
venus, raph, lina = (Character(f"OakCharacter_{n}", name) for n, name in ((2, "Venus"), (3, "Raph"), (4, "Lina")))
fifth = Character("OakCharacter_5", "Fifth")


def synced(held: roster.Roster, *pawns) -> roster.Roster:
    game.seat(*pawns)
    held.sync(players.everyone(game.world))
    return held


check("the host first in the game's list, whatever its order", [player.host for player in (
    game.seat(venus, host) or players.everyone(game.world))] == [True, False])
held = synced(roster.Roster(), host)
check("the host J1 in team 1", seats(held) == [(1, 1, True, "Kevin")] and held.where == roster.HOST)
synced(held, host, venus, raph)
check("each newcomer the smallest number and team free", seats(held) == [
    (1, 1, True, "Kevin"), (2, 2, False, "Venus"), (3, 3, False, "Raph")])
check("a team chosen", held.set_team(3, 1) and [seat.team for seat in held.seats] == [1, 2, 1])
check("the same team again: no change", not held.set_team(3, 1))
check("refused for a seat or a team that does not exist", not held.set_team(9, 2) and not held.set_team(2, 5))
check("the teams by number, each with its seats", {team: [seat.number for seat in group]
                                                  for team, group in held.groups().items()} == {1: [1, 3], 2: [2]})
synced(held, host, raph)
check("a player gone loses his seat, the others keep theirs", seats(held) == [(1, 1, True, "Kevin"),
                                                                             (3, 1, False, "Raph")])
synced(held, host, raph, lina)
check("a newcomer takes the smallest number and team free", seats(held)[1] == (2, 2, False, "Lina"))
raph.renew_state()
synced(held, host, raph, lina)
check("after a travel, a new PlayerState under the same name keeps its seat", seats(held)[2] == (3, 1, False, "Raph")
      and held.seat_of(raph.PlayerState) is held.seats[2])
held.each_alone()
check("EACH FOR THEMSELVES: the host in 1, the others after him", [seat.team for seat in held.seats] == [1, 2, 3])
synced(held, host, venus, raph, lina, fifth)
check("four seats at most", [seat.number for seat in held.seats] == [1, 2, 3, 4]
      and held.seat_of(fifth.PlayerState) is None)

game.seat(host, venus)
roster.refresh()
check("refresh reads the host's game", [seat.name for seat in roster.ROSTER.seats] == ["Kevin", "Venus"])
game.seat(Character("OakCharacter_9", "Them", role=game_fixture.PROXY), venus)
roster.refresh()
check("in a guest's game, marked so and left as it was", roster.ROSTER.where == roster.GUEST
      and len(roster.ROSTER.seats) == 2)
logged = "\n".join(state["logs"])
check("the names never in the log", "Kevin" not in logged and "Venus" not in logged)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
