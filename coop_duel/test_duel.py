"""The duel over a fake co-op game and a fake clock (duel.py, fight.py, teams.py, knockout.py, score.py, banner.py).

One against one. Refused, nothing changed: no game, a guest's game, no guest, a player without a character, a
vehicle, a team refused or not taken. Started: the guest in Team_Hostile, the score on the screen with the players'
names, which never reach the log. Each fall ends the round in one against one: the point to the other player, the
round's winner on the plate, the pause (the guest's own team back), the one who fell KO 3 s with the game's countdown
paused and no damage taken, then stood up in place, flesh and shield refilled but not the overshield, the duel resumed;
a player just stood up not asked again for a second; both falling at once, a draw. The message taken off after 4 s. A
team the game took back handed again, a duel given up when it keeps being taken. Ended, every player back to normal,
the one still KO stood up: by STOP, when the mod is switched off (no message left on the screen), and on its own when
the guest leaves (one team left), a player comes, the world changes, the game is no longer the host's, or the beat
keeps failing. A host in a vehicle is not asked. A start refused while a player is down, each refusal written with its
cause; a player the game does not stand up ending the duel; a refused give-back tried again; a guest left in the
duel's team by an earlier duel given the players' team; the last message taken off when the mod is switched off."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import game_fixture  # noqa: E402

game = game_fixture.install(state)
panel_fixture.Widget.RemoveFromParent = lambda self: setattr(self, "on_screen", False)

import coop_duel  # noqa: E402
from coop_duel import banner, duel, fight, knockout  # noqa: E402

fails: list[str] = []
now = [100.0]
duel.clock = lambda: now[0]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def at(seconds: float) -> None:
    now[0] = seconds
    duel.beat(seconds)


def lines(event: str) -> list[dict]:
    return [line for line in game_fixture.duel_lines(state) if line["event"] == event]


def team(pawn) -> str:
    return game.teams.GetTeam(pawn).name


def message() -> str:
    """The message on the screen, its texts in order joined by " | ": the title, then the score or the sentence."""
    shown = [holder for holder in game.screen.added if getattr(holder, "on_screen", False)]
    if not shown:
        return ""
    made = panel_fixture.Widget.created
    after = made[made.index(shown[-1]):]
    return " | ".join(widget.calls["SetText"][0] for widget in after if widget.kind == "TextBlock")


Host, Guest = game_fixture.Character, game_fixture.Character
host = Host("OakCharacter_1", "Kevin", local=True)
guest = Guest("OakCharacter_2", "Venus")

game.seat()
check("refused without a game's characters, nothing changed", duel.start("EN") == "no_character"
      and duel.live() is None)
game.seat(Host("OakCharacter_9", "Them", role=game_fixture.PROXY))
check("refused in a guest's game", duel.start("EN") == "not_host")
game.seat(host)
check("refused without a guest", duel.start("EN") == "no_guest")
guest.away = True
game.seat(host, guest)
check("refused while a player has no character", duel.start("EN") == "player_away")
guest.away = False
game.seat(host, game_fixture.Vehicle("Vehicle_2", driver=guest))
check("refused with the guest in a vehicle", duel.start("EN") == "in_vehicle")
game.seat(game_fixture.Vehicle("Vehicle_1", local=True, driver=host), guest)
check("refused with the host in a vehicle", duel.start("EN") == "in_vehicle")
game.seat(host, guest)
game.teams.refuse = {guest.Name}
check("refused when the game refuses the team, the guest left as he was",
      duel.start("EN") == "team_refused" and team(guest) == "Team_Player" and duel.live() is None)
game.teams.refuse, game.teams.keep_player = set(), {guest.Name}
check("refused when the team is not taken, his own team given back", duel.start("EN") == "team_refused"
      and game.teams.set_calls[-1] == (guest.Name, "Team_Player") and duel.live() is None)
game.teams.keep_player = set()
check("no SetTeam on any refusal before the guest's team is read", all(
    name == guest.Name for name, _team in game.teams.set_calls))

check("started", duel.start("EN") == "started")
check("the guest in Team_Hostile, the host left in his team", team(guest) == "Team_Hostile"
      and team(host) == "Team_Player")
check("the score on the screen with the players' names", message() == "DUEL | Kevin | 0 - 0 | Venus")
check("the window sees the duel", duel.live() == duel.View("Kevin  0 - 0  Venus"))
check("a second start refused", duel.start("EN") == "already_on")
said = lines("attitudes")[-1]
check("the attitudes said, hostile both ways", (said["a"], said["b"], said["a_to_b"], said["b_to_a"]) == (
    "J1", "J2", "2", "2"))

asked_at_start = guest.asked
at(100.05)
check("nobody asked before a step", guest.asked == asked_at_start)
guest.down = True
at(100.2)
check("a fall: the round to the other player", duel.live() == duel.View("Kevin  1 - 0  Venus")
      and lines("round")[-1]["winner"] == 1)
check("the duel paused: the guest's own team back", team(guest) == "Team_Player")
check("KO: the game's countdown paused, no damage taken", guest.pauses == [(True, knockout.PAUSE_REASON)]
      and guest.bCanBeDamaged is False)
check("the round's winner on the plate, the new score under it", message() == "ROUND 1 · KEVIN | Kevin | 1 - 0 | Venus")
at(103.1)
check("still KO before 3 s", guest.stops == [] and guest.down)
at(103.3)
check("stood up in place after 3 s", guest.stops == [game_fixture.REVIVED] and not guest.down
      and guest.pauses[-1] == (False, knockout.PAUSE_REASON))
check("flesh and shield refilled, not the overshield", [kind for _name, kind, *_rest in game.damage.refills] == [
    "HealthType_Player_Health_Flesh", "HealthType_Player_Shield_Energy"])
check("damage as before, the duel resumed in Team_Hostile", guest.bCanBeDamaged is True
      and team(guest) == "Team_Hostile" and lines("duel resumed"))
guest.down = True
at(103.5)
check("a player just stood up not asked again for a second", duel.live() == duel.View("Kevin  1 - 0  Venus"))
at(104.4)
check("asked again after a second", duel.live() == duel.View("Kevin  2 - 0  Venus"))
at(107.5)
host.down = True
at(108.6)
check("the host falls: the round to the guest, the duel paused", duel.live() == duel.View("Kevin  2 - 1  Venus")
      and team(guest) == "Team_Player" and host.bCanBeDamaged is False)
at(111.7)
check("the host stood up in place, the duel resumed", not host.down and host.stops and team(guest) == "Team_Hostile")
at(116.0)
check("the message taken off after 4 s", message() == "")

host.down = guest.down = True
at(117.0)
check("both falling at once: a draw, no point", duel.live() == duel.View("Kevin  2 - 1  Venus")
      and lines("round")[-1]["winner"] == "draw" and message() == "ROUND 4 · DRAW | Kevin | 2 - 1 | Venus")
at(120.1)
check("both stood up, the duel resumed once", not host.down and not guest.down and team(guest) == "Team_Hostile"
      and len(lines("duel resumed")) == 4)

game.teams.teams[guest.Name] = game_fixture.PLAYER
at(121.5)
check("a team the game took back handed again", team(guest) == "Team_Hostile"
      and lines("team lost, handed again")[-1]["times"] == 1)

guest.down = True
at(122.0)
check("STOP during the pause: stopped", duel.stop("stopped") == "stopped" and duel.live() is None)
check("the one still KO stood up, the guest's own team given back", not guest.down and guest.bCanBeDamaged is True
      and team(guest) == "Team_Player")
check("the final score on the screen", message() == "DUEL OVER | Kevin | 3 - 1 | Venus")
check("a second stop: not running", duel.stop("stopped") == "not_running")
logged = "\n".join(state["logs"])
check("the players' names never in the log", "Kevin" not in logged and "Venus" not in logged)


def ended_by(make, why: str) -> bool:
    game.seat(host, guest)
    game.teams.teams.clear()
    host.broken = guest.broken = False
    if duel.start("EN") != "started":
        return False
    make()
    for step in range(12):
        at(now[0] + 0.2)
    return duel.live() is None and lines("duel over")[-1]["why"] == why and team(guest) == "Team_Player"


at(200.0)
check("ended when the guest leaves: one team left", ended_by(lambda: game.seat(host), "teams_left"))
check("ended when a player comes", ended_by(lambda: game.seat(host, guest, Guest("OakCharacter_3", "C")),
                                            "player_joined"))
check("ended when the world changes", ended_by(game.travel, "world_changed"))
check("ended when the game is no longer the host's", ended_by(
    lambda: game.seat(Host("OakCharacter_9", "Them", role=game_fixture.PROXY), guest), "not_host"))


def keep_taking() -> None:
    game.teams.keep_player = {guest.Name}
    game.teams.teams[guest.Name] = game_fixture.PLAYER


check("ended when the team is no longer taken", ended_by(keep_taking, "team_lost"))
game.teams.keep_player = set()
game.teams.teams.clear()
duel.start("EN")
for _round in range(fight.MAX_HANDS + 2):
    game.teams.teams[guest.Name] = game_fixture.PLAYER
    at(now[0] + fight.TEAM_CHECK_S + 0.1)
check("given up when the game keeps taking the team back", duel.live() is None
      and lines("duel over")[-1]["why"] == "team_lost" and lines("team lost, handed again")[-1]["times"] == fight.MAX_HANDS + 1)
check("ended when the beat keeps failing", ended_by(lambda: setattr(guest, "broken", True), "error"))
guest.broken = False

game.seat(game_fixture.Vehicle("Vehicle_1", local=True, driver=host), guest)
game.teams.teams.clear()
game.seat(host, guest)
duel.start("EN")
game.seat(game_fixture.Vehicle("Vehicle_1", local=True, driver=host), guest)
at(now[0] + 0.2)
at(now[0] + 0.2)
check("a host in a vehicle is not asked, the duel goes on", duel.live() is not None
      and duel._live["duel"].failed == 0)
game.seat(host, guest)
at(now[0] + 0.2)
coop_duel.mod.disable()
check("the mod switched off: the duel ended, the guest's team given back", duel.live() is None
      and lines("duel over")[-1]["why"] == "mod_off" and team(guest) == "Team_Player")
check("and no message left on the screen", message() == "")
coop_duel.mod.enable()
check("the banner's time on the screen is 4 s", banner.SHOW_S == 4.0)

game.seat(host, guest)
game.teams.teams.clear()
guest.down = True
check("refused while a player is already down, the refusal written with its cause",
      duel.start("EN") == "player_down" and lines("duel not started")[-1]["why"] == "player_down")
guest.down = False

duel.start("EN")
guest.down, guest.stuck = True, True
for _step in range(40):
    at(now[0] + 0.2)
check("a player the game does not stand up ends the duel, his damage and team given back", duel.live() is None
      and lines("duel over")[-1]["why"] == "stand_up_failed" and guest.bCanBeDamaged is True
      and team(guest) == "Team_Player")
guest.down = guest.stuck = False

duel.start("EN")
game.teams.refuse = {guest.Name}
duel.stop("stopped")
check("a give-back the game refuses leaves the guest in the duel's team for now", team(guest) == "Team_Hostile")
at(now[0] + 0.5)
game.teams.refuse = set()
at(now[0] + duel.RETURN_EVERY_S + 0.1)
check("and is tried again until his own team is back", team(guest) == "Team_Player" and duel._return["members"] == [])

duel.start("EN")
game.teams.keep_player = {guest.Name}
duel.stop("stopped")
check("a give-back the game takes without applying it is tried again", duel._return["members"] != [])
for _try in range(duel.MAX_RETURNS - 1):
    at(now[0] + duel.RETURN_EVERY_S + 0.1)
game.teams.keep_player = set()
at(now[0] + duel.RETURN_EVERY_S + 0.1)
check("the last try that works is not said to have failed", team(guest) == "Team_Player"
      and duel._return["members"] == [] and not lines("team never given back"))

game.teams.teams[guest.Name] = game_fixture.Handle(game_fixture.TEAM_KIND, "Team_Hostile")
duel.start("EN")
duel.stop("stopped")
check("a guest left in the duel's team by an earlier duel gets the players' team back", team(guest) == "Team_Player"
      and lines("own team was the duel's"))

at(now[0] + 10.0)
duel.start("EN")
duel.stop("stopped")
coop_duel.mod.disable()
check("switched off with no duel, the last message taken off at once", message() == "")
coop_duel.mod.enable()

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
