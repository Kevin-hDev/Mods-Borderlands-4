"""The duel between three and four players over the fake game (docs/duel/spec-equipes.md): each for themselves at
three, each guest in his own team of the game (Team_Hostile, then Team_Bandit), every pair's attitude and each player
said in the log; a fall with two teams standing going on, the player down protected and keeping his duel team; the
last team standing winning, named on the plate; the pause for every guest; a draw; a player who comes ending the duel,
said on the screen. Two against two: the host's teammate in the players' team, the others sharing Team_Hostile; a
player stood up by his teammate back in the round, countdown and damage as before; a player who leaves leaving the
duel, which goes on; the last of a team leaving ending it. One against three. Each for themselves at four, the four
teams of the game. Refused with everyone in one team. A player knocked down during the pause protected, no point
given, stood up with the others, and when the duel is stopped then; the cause written before the last calls. A start
the game refuses at three, a refused give-back tried again; the mod switched off, one tried once more and written down.
Long names cut on the line. The players' names never in the log."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import game_fixture  # noqa: E402

game = game_fixture.install(state)
panel_fixture.Widget.RemoveFromParent = lambda self: setattr(self, "on_screen", False)

import coop_duel  # noqa: E402,F401
from coop_duel import duel, knockout, panel_en, roster  # noqa: E402

fails: list[str] = []
now = [100.0]
duel.clock = lambda: now[0]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def later(seconds: float) -> None:
    now[0] += seconds
    duel.beat(now[0])


def lines(event: str) -> list[dict]:
    return [line for line in game_fixture.duel_lines(state) if line["event"] == event]


def team(pawn) -> str:
    return game.teams.GetTeam(pawn).name


def message() -> str:
    shown = [holder for holder in game.screen.added if getattr(holder, "on_screen", False)]
    if not shown:
        return ""
    made = panel_fixture.Widget.created
    after = made[made.index(shown[-1]):]
    return " | ".join(widget.calls["SetText"][0] for widget in after if widget.kind == "TextBlock")


def fresh(*pawns) -> None:
    """A new game: no duel, every player standing in his own team, then these players seated, each alone in his
    team."""
    duel.stop("stopped", show=False)
    game.teams.teams.clear()
    for pawn in pawns:
        pawn.down = False
    roster.ROSTER.seats.clear()
    game.seat(*pawns)
    roster.refresh()
    later(10.0)


Character = game_fixture.Character
host = Character("OakCharacter_1", "Kevin", local=True)
venus, raph, lina = (Character(f"OakCharacter_{n}", name) for n, name in ((2, "Venus"), (3, "Raph"), (4, "Lina")))

fresh(host, venus, raph)
check("each for themselves at first: J1 to J3 in teams 1 to 3", [
    (seat.number, seat.team) for seat in roster.ROSTER.seats] == [(1, 1), (2, 2), (3, 3)])
check("started at three", duel.start("EN") == "started")
check("the host left in his team, each guest in his own team of the game", team(host) == "Team_Player"
      and team(venus) == "Team_Hostile" and team(raph) == "Team_Bandit")
check("the message: each team followed by its points", message() == "DUEL | Kevin | 0 | · | Venus | 0 | · | Raph | 0")
pairs = {(line["a"], line["b"]): (line["a_to_b"], line["b_to_a"]) for line in lines("attitudes")}
check("every pair's attitude said, the two guests hostile to each other", pairs == {
    ("J1", "J2"): ("2", "2"), ("J1", "J3"): ("2", "2"), ("J2", "J3"): ("2", "2")})
check("each player said with his duel team and the game's", [(line["player"], line["team"], line["given"])
                                                            for line in lines("player")] == [
    ("J1", 1, "Team_Player"), ("J2", 2, "Team_Hostile"), ("J3", 3, "Team_Bandit")])
check("the duel's start said with the version and the size of each team", lines("duel starting")[-1]["teams"] == [
    1, 1, 1] and lines("duel starting")[-1]["version"] == coop_duel.__version__)
venus.down = True
later(0.2)
check("one down, two teams standing: the round goes on, he keeps his duel team, protected", duel.live() == duel.View(
    "Kevin  0  ·  Venus  0  ·  Raph  0") and team(venus) == "Team_Hostile" and venus.bCanBeDamaged is False
      and venus.pauses[-1] == (True, knockout.PAUSE_REASON) and lines("standing")[-1]["teams"] == {
    "1": 1, "2": 0, "3": 1})
raph.down = True
later(0.2)
check("the last team standing wins the round", duel.live() == duel.View("Kevin  1  ·  Venus  0  ·  Raph  0")
      and lines("round")[-1]["winner"] == 1)
check("the round's winner named on the plate", message().startswith("ROUND 1 · KEVIN | "))
check("the pause: every guest given his own team back", team(venus) == team(raph) == "Team_Player")
later(3.1)
check("everyone down stood up, the duel's teams handed again", not venus.down and not raph.down
      and team(venus) == "Team_Hostile" and team(raph) == "Team_Bandit" and venus.bCanBeDamaged is True)
later(1.1)
host.down = venus.down = raph.down = True
later(0.2)
check("the last ones falling at the same step: a draw, no point", duel.live() == duel.View(
    "Kevin  1  ·  Venus  0  ·  Raph  0") and lines("round")[-1]["winner"] == "draw"
      and message().startswith("ROUND 2 · DRAW | "))
later(3.1)
later(1.1)
game.seat(host, venus, raph, lina)
later(0.2)
check("a player who comes ends the duel, said on the screen, every guest given his team back", duel.live() is None
      and lines("duel over")[-1]["why"] == "player_joined" and lines("player joined")[-1]["characters"] == [
          "OakCharacter_4"]
      and message() == f"DUEL OVER | {panel_en.TEXT['stop_player_joined']}"
      and team(venus) == team(raph) == "Team_Player")

fresh(host, venus, raph, lina)
roster.ROSTER.set_team(3, 1)
roster.ROSTER.set_team(4, 2)
check("two against two started", duel.start("EN") == "started")
check("the host's teammate in the players' team, the other two sharing Team_Hostile", team(raph) == "Team_Player"
      and team(venus) == team(lina) == "Team_Hostile")
check("the message: each team's names joined around the points",
      message() == "DUEL | Kevin + Raph | 0 - 0 | Venus + Lina")
pairs = {(line["a"], line["b"]): (line["a_to_b"], line["b_to_a"]) for line in lines("attitudes")[-6:]}
# Team_Hostile reads hostile to its own members, as the game does (trial 1), yet they share a collision channel and do
# not hurt each other.
check("the host's teammates friends, opponents hostile, Team_Hostile's members read hostile",
      pairs[("J1", "J3")] == ("0", "0") and pairs[("J1", "J2")] == ("2", "2") and pairs[("J2", "J4")] == ("2", "2"))
venus.down = True
later(0.2)
check("a fall with a teammate standing: the round goes on",
      duel.live() == duel.View("Kevin + Raph  0 - 0  Venus + Lina"))
venus.down = False
later(0.2)
check("stood up by her teammate: back in the round, countdown and damage as before",
      lines("stood up in the round")[-1]["player"] == "J2" and venus.pauses[-1] == (False, knockout.PAUSE_REASON)
      and venus.bCanBeDamaged is True and team(venus) == "Team_Hostile")
venus.down = lina.down = True
later(0.2)
check("both down: the other team wins, named on the plate", duel.live() == duel.View(
    "Kevin + Raph  1 - 0  Venus + Lina") and message().startswith("ROUND 1 · TEAM 1 | "))
later(3.1)
later(1.1)
game.seat(host, venus, raph)
later(0.2)
check("a player who leaves leaves the duel, which goes on with two teams", duel.live() == duel.View(
    "Kevin + Raph  1 - 0  Venus") and lines("player left")[-1]["player"] == "J4")
game.seat(host, raph)
later(0.2)
check("the last of a team leaving ends the duel, said on the screen", duel.live() is None
      and lines("duel over")[-1]["why"] == "teams_left"
      and message() == f"DUEL OVER | {panel_en.TEXT['stop_teams_left']}" and team(raph) == "Team_Player")

fresh(host, venus, raph, lina)
for number in (2, 3, 4):
    roster.ROSTER.set_team(number, 2)
check("one against three started, the three sharing Team_Hostile", duel.start("EN") == "started"
      and team(venus) == team(raph) == team(lina) == "Team_Hostile")
check("the message: the host alone against three", message() == "DUEL | Kevin | 0 - 0 | Venus + Raph + Lina")
host.down = True
later(0.2)
check("the host down: the three win", duel.live() == duel.View("Kevin  0 - 1  Venus + Raph + Lina")
      and message().startswith("ROUND 1 · TEAM 2 | "))

fresh(host, venus, raph, lina)
check("each for themselves at four: the four teams of the game", duel.start("EN") == "started"
      and [team(pawn) for pawn in (host, venus, raph, lina)] == [
          "Team_Player", "Team_Hostile", "Team_Bandit", "Team_Order"])

fresh(host, venus, raph)
roster.ROSTER.set_team(2, 1)
roster.ROSTER.set_team(3, 1)
made = len(game.teams.set_calls)
check("refused with everyone in one team, nothing changed", duel.start("EN") == "one_team"
      and len(game.teams.set_calls) == made)

fresh(host, venus)
duel.start("EN")
venus.down = True
later(0.2)
host.down = True
later(0.2)
check("knocked down during the pause by an enemy around: protected, no point given", host.bCanBeDamaged is False
      and host.pauses[-1] == (True, knockout.PAUSE_REASON) and duel.live() == duel.View("Kevin  1 - 0  Venus"))
later(3.1)
check("stood up with the others at the pause's end, the next round on", not host.down and not venus.down
      and host.bCanBeDamaged is True and team(venus) == "Team_Hostile")
later(1.1)
venus.down = True
later(0.2)
host.down = True
later(0.2)
duel.stop("stopped")
logged = game_fixture.duel_lines(state)
ending = max(index for index, line in enumerate(logged) if line["event"] == "duel ending")
check("stopped during the pause: the player knocked down in it stood up too", not host.down and not venus.down)
check("the cause written before the duel's last calls", logged[ending]["why"] == "stopped" and any(
    line["event"] == "team given back" for line in logged[ending:]) and logged[-1]["event"] == "duel over")

fresh(host, venus, raph)
real_set = game.teams.SetTeam
refused = {"once": True}


def set_team(actor, handle) -> None:
    """Venus's first give-back refused by the game."""
    if actor.Name == venus.Name and handle.name == "Team_Player" and refused["once"]:
        refused["once"] = False
        raise RuntimeError("refused")
    real_set(actor, handle)


game.teams.SetTeam = set_team
game.teams.keep_player = {raph.Name}
check("a start the game refuses at three, a guest's give-back refused", duel.start("EN") == "team_refused"
      and team(venus) == "Team_Hostile")
game.teams.SetTeam, game.teams.keep_player = real_set, set()
later(1.1)
check("the refused give-back tried again, as at a duel's end", team(venus) == "Team_Player")

fresh(host, venus)
duel.start("EN")
game.teams.refuse = {venus.Name}
coop_duel._on_disable()
check("the mod switched off with a give-back refused: tried once more, written down",
      lines("team not given back, mod off")[-1]["player"] == "J2" and team(venus) == "Team_Hostile")
game.teams.refuse = set()
later(1.1)
check("tried again by the beat once the mod is back on", team(venus) == "Team_Player")

longest = Character("OakCharacter_5", "Abcdefghijklmnopq")
fresh(host, venus, longest)
duel.start("EN")
check("past two players, a long name cut on the line", "Abcdefghijklmn…" in duel.live().line)
duel.stop("stopped")
logged = "\n".join(state["logs"])
check("the players' names never in the log", not any(name in logged for name in (
    "Kevin", "Venus", "Raph", "Lina", "Abcdefghijklmn")))

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
