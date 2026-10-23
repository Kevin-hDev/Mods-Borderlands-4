"""Tests a companion's follow (companions/follow.py), joined through the team (team.py), It Follows' modules faked
(companion_fixture.py), its parts each tested alone too. Taken from the trials' test of the follow
(docs/renforts/sondes/test_run_renforts_follow.py).

The start: its zone widened, its speed bonus raised, its health a multiple of the hunter's by the level It Follows
plays, with a shield, its staggers locked; said by report.py. Its card's choice: its bonus at +30 % or off, no shield.
No health pool read at its start (trial 190): its health tried again at the next HARDEN_TRIES samples, the outcome
said once. A sample a second: the zone moved onto the hunter once he
is FOLLOW_M away, at most every FOLLOW_S, his vehicle while he drives; walked to him beyond WALK_M, its run locked,
pushed to its own place within PUSH_M, the walk aborted within ARRIVAL_M, between samples too, its walk locked then
freed; teleported behind him when left too far, once he stands on ground, never while it fights within
FIGHT_TELEPORT_M; a blocked walk ended by a teleport; the nearest enemy imposed as its target, its walks stopped unless
it stands beyond LEASH_M. The end at its death (read dead, or downed then hidden or taken away), its loss, its zone
gone or refused TRIES times, an error, or the team's stop, once: the walk aborted, the target cleared, the bonus and
the radius written back, the zone put back, said; a death tells the team."""

import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
from it_follows.companions import catch, choices, follow, kinds, team as team_module  # noqa: E402

fails: list[str] = []
FRAME = "Char_TedioreFrame_NoVacancy_Side"
# The team is asked by name (kinds.py); the allies are each one definition.
NAME_OF = {kind.definition: kind.name for kind in kinds.ALLIES}


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    """report.py's lines of that event, in order."""
    found = [json.loads(text.removeprefix("[It Follows] ")) for text in state["info"]
             if text.startswith("[It Follows] {")]
    return [line for line in found if line["event"] == event]


def begun(at: tuple = (1000.0, 0.0, 0.0), definition: str = "Char_NPC_Abomination") -> tuple:
    """A game, a companion born of OakSpawner_1, joined by a team: (game, companion, its follow, team, clock)."""
    state["info"].clear()
    game = fake.Game(state)
    clock = fake.Clock()
    companion = game.companion(1, at, definition)
    team = team_module.Team(clock, fake.Births(game))
    answer = team.join(NAME_OF[definition], "OakSpawner_1", None)
    return game, companion, (team.follows[-1] if answer["done"] == "started" else answer), team, clock


def at(clock: fake.Clock, moment: float, one: follow.Follow) -> None:
    clock.now = moment
    one.beat()


game, companion, one, team, clock = begun()
start = notes("companion_start")[-1]
check("the start said: its zone widened, its speed raised, its health at God by the hunter's, a shield, its staggers "
      "locked", start == {
          "event": "companion_start", "run": 0, "character": "Char_NPC_Abomination_1",
          "companion": "Abomination", "rank": 0, "radius": "15.0->40.0", "boost": "1.0->1.2",
          "tough": {"level": ["God", "normal"], "hunter": 83, "health": {"0": [100, 1000]}, "shield": [1, 125, 300]},
          "calm": ["Flinch", "Stagger", "Launch"]})
check("the values trial 88 listed, locked for good", [lock[1:] for lock in game.locks] == [
      (1, True), (2, True), (3, True)])
check("its zone widened, its health raised and full", companion.zone.settings.CombatTerritory.Radius == 4000.0
      and companion.pools == {0: 1000.0, 1: 300.0} and "share 0 1.0" in fake.calls and "share 1 1.0" in fake.calls
      and abs(companion.CharacterMovement.MaxGroundSpeedScale.Value - 1.2) < 1e-9)

at(clock, 100.5, one)
check("nothing before a second", one.samples == 0 and companion.zone.moves == [])
at(clock, 101.0, one)
check("the zone moved onto the hunter, teleported, no sweep", companion.zone.at == (0.0, 0.0, 0.0)
      and companion.zone.moves[0] == ((0.0, 0.0, 0.0), False, True) and one.samples == 1)
at(clock, 101.0, one)
check("one sample a second, however many images", one.samples == 1)
check("no sample written: It Follows writes none of the calls made every second", notes("call") == [])

game.hunter.where = (3100.0, 0.0, 0.0)
at(clock, 102.0, one)
check("walked as soon as it is beyond WALK_M, the zone not again within FOLLOW_S", companion.zone.at == (
      0.0, 0.0, 0.0) and [walk[:2] for walk in game.brain.walks] == [(companion, game.hunter)])
check("its run locked as it walks", "lock Renforts True Stance_Run" in fake.calls)
at(clock, 103.0, one)
check("followed once FOLLOW_S has gone; one walk at a time", companion.zone.at == (3100.0, 0.0, 0.0)
      and len(game.brain.walks) == 1)
car = fake.character("Car", "Car", (9000.0, 0.0, 0.0))
state["pc"].Pawn = car
at(clock, 105.0, one)
check("the vehicle followed while the hunter drives", companion.zone.at == (9000.0, 0.0, 0.0))
state["pc"].Pawn = None
companion.where = (3200.0, 0.0, 0.0)
at(clock, 106.0, one)
check("the walk aborted within ARRIVAL_M", game.brain.aborts == [companion] and not one.walker.walking)
check("its walk locked then freed once arrived", fake.calls[-3:] == [
      "unlock Renforts", "lock Renforts True Stance_Walk", "unlock Renforts"])
team.stop("stopped")
end = notes("companion_end")[-1]
check("the end said, the zone put back, the bonus and the radius written back", end["why"] == "stopped"
      and end["zone_back"] == "restored" and companion.zone.at == (50000.0, 0.0, 0.0)
      and end["pace_back"] == {"stance": "not_locked", "boost": "restored"}
      and companion.CharacterMovement.MaxGroundSpeedScale.Value == 1.0 and end["radius_back"] == "restored"
      and companion.zone.settings.CombatTerritory.Radius == 1500.0 and end["walks"] == 1
      and end["target_back"] == "inactive" and end["seconds"] == 6)
check("stopped: taken out of the world by GbxDestroyActor(False), after all was given back, never called back "
      "(decision 59)", end["removed"] == "removed" and "remove Char_NPC_Abomination_1 False" in fake.calls
      and notes("call")[-1] == {"event": "call", "run": 0, "call": "GbxDestroyActor", "on": "Char_NPC_Abomination_1"}
      and not team.respawns.pending() and not notes("companion_recalled"))
moves = len(companion.zone.moves)
one.finish("again")
check("the end only once", notes("companion_end")[-1]["why"] == "stopped" and len(companion.zone.moves) == moves)
at(clock, 200.0, one)
check("nothing after the end", one.samples == 5)

game, companion, one, team, clock = begun()
game.hunter.where = (3100.0, 0.0, 0.0)
at(clock, 101.0, one)
companion.where = (1500.0, 0.0, 0.0)
at(clock, 101.1, one)
check("between samples, beyond ARRIVAL_M: the walk goes on", one.walker.walking and one.samples == 1)
companion.where = (2300.0, 0.0, 0.0)
at(clock, 101.15, one)
check("not asked again within ARRIVAL_EVERY_S", one.walker.walking)
at(clock, 101.3, one)
check("between samples, within ARRIVAL_M: the walk aborted there", not one.walker.walking
      and game.brain.aborts == [companion] and one.samples == 1)
companion.destroyed = True
at(clock, 101.6, one)
check("no walk: nothing asked between samples; gone, the next sample ends it", not one.done
      and (at(clock, 102.0, one), notes("companion_end")[-1]["why"])[1] == "character_gone")

game, companion, one, team, clock = begun()
game.hunter.where = (2700.0, 0.0, 0.0)
at(clock, 101.0, one)
check("within PUSH_M: pushed, no walk of the game", game.brain.walks == [] and one.walker.push.active)
at(clock, 101.004, one)
check("between samples, pushed toward its place on the ARRIVAL_M circle, on its side, forced", fake.pushes == [
      ("Char_NPC_Abomination_1", 1.0, 0.0, 0.0, 1.0, True)])
at(clock, 101.01, one)
check("not pushed again within PUSH_S", len(fake.pushes) == 1)
at(clock, 101.012, one)
check("pushed again once PUSH_S has gone", len(fake.pushes) == 2)
companion.where = (1750.0, 0.0, 0.0)
at(clock, 101.02, one)
check("within ARRIVAL_M: the push stopped, nothing called", len(fake.pushes) == 2 and game.brain.aborts == []
      and not one.walker.walking)
team.stop("stopped")

game, companion, one, team, clock = begun()
game.hunter.yaw = 90.0
for second, where in ((101, 0.0), (102, 3000.0), (103, 6000.0), (104, 9000.0)):
    game.hunter.where = (where, 0.0, 0.0)
    at(clock, float(second), one)
check("left beyond TELEPORT_M: teleported behind the hunter, where he faces away", one.catch.teleports == 1
      and abs(companion.where[0] - 9000.0) < 1e-6 and abs(companion.where[1] + 1000.0) < 1e-6)
check("its distance read again after the teleport: arrived, no walk given", not one.walker.walking
      and game.brain.walks == [])
team.stop("stopped")
check("teleports counted at the end", notes("companion_end")[-1]["teleports"] == 1)
game, companion, one, team, clock = begun()
for second, where, mode in ((101, 0.0, "MOVE_Walking"), (102, 3000.0, "MOVE_Falling"), (103, 6000.0, "MOVE_Falling"),
                            (104, 9000.0, "MOVE_Falling")):
    game.hunter.where = (where, 0.0, 0.0)
    game.hunter.CharacterMovement.MovementMode = mode
    at(clock, float(second), one)
check("the hunter in the air: the companion waits for him to land", companion.where == (1000.0, 0.0, 0.0)
      and one.catch.teleports == 0)
game.hunter.CharacterMovement.MovementMode = "MOVE_Walking"
at(clock, 105.0, one)
check("landed: brought behind him, never back where it started", abs(companion.where[0] - 8000.0) < 1e-6)
team.stop("stopped")

game, companion, one, team, clock = begun()
game.hunter.where = (4000.0, 0.0, 0.0)
for second in (101, 102, 103):
    at(clock, float(second), one)
check("the game's walk not moving it, before STUCK_S: no teleport", companion.where == (1000.0, 0.0, 0.0))
at(clock, 104.0, one)
check("not moved 1 m in STUCK_S while walking: teleported to its place behind the hunter",
      abs(companion.where[0] - 3000.0) < 1e-6 and one.catch.teleports == 1)
team.stop("stopped")
game, companion, one, team, clock = begun()
game.hunter.where = (4000.0, 0.0, 0.0)
at(clock, 101.0, one)
one.walker.block.Exec = 2
for second in (102, 103, 104, 105):
    at(clock, float(second), one)
check("its walk ended by the game: not taken for a blocked one", companion.where == (1000.0, 0.0, 0.0))
team.stop("stopped")

game, companion, one, team, clock = begun()
far_bandit = game.enemy("Char_Bandit_9", (1500.0, 0.0, 0.0))
game.hunter.where = (9000.0, 0.0, 0.0)
for second in (101, 102, 103, 104):
    at(clock, float(second), one)
check("fighting 80 m from the hunter: never teleported, walked back", one.fight.foe_name == "Char_Bandit_9"
      and companion.where == (1000.0, 0.0, 0.0) and len(game.brain.walks) == 1 and one.catch.teleports == 0)
team.stop("stopped")
game, companion, one, team, clock = begun()
game.actors.append(far_bandit)
game.hunter.where = (12000.0, 0.0, 0.0)
at(clock, 101.0, one)
check("fighting 110 m from the hunter: teleported behind him", abs(companion.where[0] - 11000.0) < 1e-6)
at(clock, 102.0, one)
check("then its far enemy let go", not one.fight.fighting and "clear" in fake.calls)
team.stop("stopped")

game, companion, one, team, clock = begun()
bandit = game.enemy("Char_Bandit_1", (2500.0, 0.0, 0.0))
game.hunter.where = (3000.0, 0.0, 0.0)
at(clock, 101.0, one)
check("an enemy near: imposed as its target, no walk while it fights", "target Char_Bandit_1" in fake.calls
      and game.brain.walks == [] and one.fight.foe_name == "Char_Bandit_1")
check("its combat walk locked while it fights", fake.calls[-1] == "lock Renforts True Stance_Walk")
game.hunter.where = (6000.0, 0.0, 0.0)
at(clock, 102.0, one)
check("beyond LEASH_M it is walked back, still fighting", one.fight.foe_name == "Char_Bandit_1"
      and len(game.brain.walks) == 1)
bandit.HealthState.bCurrentlyDead = True
at(clock, 103.0, one)
check("the enemy dead: the target cleared", not one.fight.fighting and fake.calls[-1] == "clear")
bandit.HealthState.bCurrentlyDead = False
at(clock, 104.0, one)
team.stop("stopped")
check("the target cleared at the end, the targets counted", notes("companion_end")[-1]["target_back"] == "restored"
      and notes("companion_end")[-1]["targets"] == 2)

game, companion, one, team, clock = begun()
fake.at_level(None)
second = game.companion(2, (1100.0, 0.0, 0.0))
team.join("Abomination", "OakSpawner_2", None)
check("It Follows playing no level: Bandit's, 4 times the hunter's health, said with why, no refill",
      notes("companion_start")[-1]["tough"]["level"] == ["Bandit", "off"]
      and math.isclose(second.pools[0], 4 * 1000.0 / 12) and team.follows[-1].tough.refill_after_s is None)
team.stop("stopped")
game, companion, one, team, clock = begun()
state["classes"]["GbxAttributeBlueprintLibrary"].ClassDefaultObject.GetValueOfAttribute = (
    lambda name, actor, default: default)
other = game.companion(2, (1100.0, 0.0, 0.0))
team.join("Abomination", "OakSpawner_2", None)
check("the hunter's health unread: said, the companion's left as the game gives it",
      notes("companion_start")[-1]["tough"] == {"level": ["God", "normal"], "hunter": "unread:-1.0",
                                                 "health": "not_written", "shield": "none"}
      and not hasattr(other, "pools"))
team.stop("stopped")

game, companion, one, team, clock = begun()
object.__setattr__(companion, "shield", 0.0)
at(clock, 101.0, one)
at(clock, 145.0, one)
check("at God, its shield broken: not filled before 45 s", "refill 7.69" not in fake.calls)
at(clock, 146.0, one)
check("then filled again, each sample keeping it", "refill 7.69" in fake.calls and one.tough.refills == 1)
team.stop("stopped")
check("its fills counted at the end", notes("companion_end")[-1]["refills"] == 1)

game, companion, one, team, clock = begun()
at(clock, 101.0, one)
companion.HealthState.bCurrentlyDead = True
at(clock, 102.0, one)
check("dead: the end, the zone put back, the team told", notes("companion_end")[-1]["why"] == "character_dead"
      and companion.zone.at == (50000.0, 0.0, 0.0) and team.respawns.pending()
      and notes("companion_dead")[-1]["companion"] == "Abomination")
check("dead: left to the game, never removed, never recalled", notes("companion_end")[-1]["removed"] is None
      and not any(call.startswith("remove") for call in fake.calls) and not notes("companion_recalled"))
game, companion, one, team, clock = begun()
companion.destroyed = True
at(clock, 101.0, one)
check("gone (a map change): the end, nothing to remove, called back near the hunter (decision 59)",
      notes("companion_end")[-1]["why"] == "character_gone" and notes("companion_end")[-1]["removed"] == "gone"
      and team.respawns.pending() and notes("companion_recalled")[-1] == {
          "event": "companion_recalled", "run": 0, "companion": "Abomination", "why": "character_gone",
          "recalls": 1} and notes("companion_called")[-1]["companion"] == "Abomination")
for again in range(2, team_module.RECALLS_MOST + 1):
    team.respawns.clear()
    companion = game.companion(again, (1000.0, 0.0, 0.0), "Char_NPC_Abomination")
    team.join("Abomination", f"OakSpawner_{again}", None)
    clock.now += 1.0
    companion.destroyed = True
    at(clock, clock.now + 1.0, team.follows[-1])
team.respawns.clear()
companion = game.companion(9, (1000.0, 0.0, 0.0), "Char_NPC_Abomination")
team.join("Abomination", "OakSpawner_9", None)
companion.destroyed = True
at(clock, clock.now + 2.0, team.follows[-1])
check("gone at each birth: recalled RECALLS_MOST times in a row, then no more, said",
      len(notes("companion_recalled")) == team_module.RECALLS_MOST and not team.respawns.pending()
      and notes("companion_not_recalled")[-1]["recalls"] == team_module.RECALLS_MOST)
team.respawns.clear()
companion = game.companion(10, (1000.0, 0.0, 0.0), "Char_NPC_Abomination")
team.join("Abomination", "OakSpawner_10", None)
start_at = clock.now
companion.destroyed = True
at(clock, start_at + team_module.RECALL_KEPT_S + 1.0, team.follows[-1])
check("after a follow of RECALL_KEPT_S, the count forgotten: called back again",
      notes("companion_recalled")[-1]["recalls"] == 1 and team.respawns.pending())
game, companion, one, team, clock = begun(definition=FRAME)
object.__setattr__(companion, "left", {0: 0.0})
at(clock, 101.0, one)
check("trial 186: downed, followed on, no death yet", not one.done and not team.respawns.pending())
companion.where = (40.0, -30.0, 800.0)
at(clock, 102.0, one)
check("downed then hidden at the origin: dead, coming back", notes("companion_end")[-1]["why"] == "character_dead"
      and team.respawns.pending())
game, companion, one, team, clock = begun(definition=FRAME)
object.__setattr__(companion, "left", {0: 0.0})
at(clock, 101.0, one)
object.__setattr__(companion, "left", {0: 0.3})
at(clock, 102.0, one)
companion.destroyed = True
at(clock, 103.0, one)
check("downed, revived, then taken away: dead, coming back", notes("companion_end")[-1]["why"] == "character_dead"
      and team.respawns.pending())

game, companion, one, team, clock = begun()
at(clock, 101.0, one)
companion.zone.destroyed = True
at(clock, 102.0, one)
check("the zone gone: the end, nothing to put back", notes("companion_end")[-1]["why"] == "zone_gone"
      and notes("companion_end")[-1]["zone_back"] == "unavailable")
check("the zone gone, the companion still there: taken out of the world, then called back",
      notes("companion_end")[-1]["removed"] == "removed" and companion.destroyed
      and notes("companion_recalled")[-1]["why"] == "zone_gone" and team.respawns.pending())
game, companion, one, team, clock = begun()
one.pace.put_back = lambda: (_ for _ in ()).throw(RuntimeError("pace"))
team.stop("stopped")
end = notes("companion_end")[-1]
check("one give-back failing: said, the others and the removal done all the same",
      end["pace_back"] == "failed:RuntimeError:pace" and end["radius_back"] == "restored"
      and end["removed"] == "removed")
game, companion, one, team, clock = begun()
object.__setattr__(companion, "refuse_removal", True)
team.stop("stopped")
check("a removal refused: said, the stop goes on to its end", notes("companion_end")[-1]["removed"]
      == "failed:RuntimeError:refused" and notes("team_stop")[-1]["following"] == 1 and team.hook is None)
game, companion, one, team, clock = begun()
companion.zone.stuck = True
for second, where in ((101, 0.0), (103, 3000.0), (105, 6000.0)):
    game.hunter.where = (where, 0.0, 0.0)
    at(clock, float(second), one)
check("TRIES moves refused in a row: the end", notes("companion_end")[-1]["why"] == "zone_refused"
      and notes("companion_end")[-1]["zone_back"] == "restored")
game, companion, one, team, clock = begun()
companion.zone.broken = True
at(clock, 101.0, one)
check("an error: said, the end", notes("companion_error")[-1]["error"].startswith("RuntimeError")
      and notes("companion_end")[-1]["why"] == "error"
      and notes("companion_end")[-1]["zone_back"] == "restore_error:RuntimeError")
game, companion, one, team, clock = begun()
check("never moved: nothing put back", (team.stop("stopped"), notes("companion_end")[-1]["zone_back"])[1]
      == "never_moved" and companion.zone.moves == [])

game, companion, one, team, clock = begun()
late = game.companion(2, (1100.0, 0.0, 0.0))
object.__setattr__(late, "kinds", [])
team.join("Abomination", "OakSpawner_2", None)
later = team.follows[-1]
check("trial 190: no health pool read at its start: said, its health tried again", notes("companion_start")[-1][
      "tough"]["health"] == "no_pool" and later.harden_left == follow.HARDEN_TRIES and not hasattr(late, "pools"))
object.__setattr__(late, "kinds", ["HealthType_AI_Flesh"])
at(clock, 101.5, later)
check("read at the next sample: its health written then, said once with the tries", notes("companion_tough") == [{
      "event": "companion_tough", "run": 0, "character": "Char_NPC_Abomination_2", "tries": 1,
      "tough": {"level": ["God", "normal"], "hunter": 83, "health": {"0": [100, 1000]}, "shield": [1, 125, 300]}}]
      and late.pools == {0: 1000.0, 1: 300.0} and later.harden_left == 0)
at(clock, 102.5, later)
check("not tried again once written", len(notes("companion_tough")) == 1)
never = game.companion(3, (1100.0, 0.0, 0.0))
object.__setattr__(never, "kinds", [])
team.join("Abomination", "OakSpawner_3", None)
last = team.follows[-1]
for moment in range(1, follow.HARDEN_TRIES):
    at(clock, 103.0 + moment, last)
check("still none: tried again quietly", notes("companion_tough") == notes("companion_tough")[:1]
      and last.harden_left == 1)
at(clock, 103.0 + follow.HARDEN_TRIES, last)
at(clock, 104.0 + follow.HARDEN_TRIES, last)
check("none at the last try: said with what was read, never tried again", notes("companion_tough")[-1]["tries"]
      == follow.HARDEN_TRIES and notes("companion_tough")[-1]["tough"]["health"] == "no_pool"
      and notes("companion_tough")[-1]["tough"]["types"] == [] and len(notes("companion_tough")) == 2
      and last.harden_left == 0)
team.stop("stopped")

game, companion, one, team, clock = begun()
team.picks = {"Abomination": choices.Choice(False, "+30%")}
picked = game.companion(2, (1100.0, 0.0, 0.0))
team.join("Abomination", "OakSpawner_2", None)
check("its card's choice: its speed raised by +30 %, no shield", notes("companion_start")[-1]["boost"] == "1.0->1.3"
      and notes("companion_start")[-1]["tough"]["shield"] == "off" and picked.pools == {0: 1000.0})
team.picks = {"Abomination": choices.Choice(True, "Off")}
still = game.companion(3, (1100.0, 0.0, 0.0))
team.join("Abomination", "OakSpawner_3", None)
check("its speed bonus off: nothing written, nothing given back", notes("companion_start")[-1]["boost"] == "off"
      and still.CharacterMovement.MaxGroundSpeedScale.Value == 1.0
      and (team.stop("stopped"), notes("companion_end")[-1]["pace_back"]["boost"])[1] == "not_boosted")

game, companion, first, team, clock = begun()
game.hunter.where = (2700.0, 0.0, 0.0)
second = game.companion(2, (1000.0, 300.0, 0.0))
team.join("Abomination", "OakSpawner_2", None)
mate = team.follows[-1]
check("a second one: its rank, its samples shifted from the first one's", mate.rank == 1
      and mate.catch.rank == 1 and mate.next == 101.0 + 1.0 / team_module.MOST)
for moment in (101.0, 101.125, 101.2):
    clock.now = moment
    team.beat()
check("its place turned by its rank's step", abs(mate.walker.push.aim - (
      math.degrees(math.atan2(300.0, -1700.0)) + catch.SPREAD_DEG)) < 1e-6)
team.stop("stopped")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
