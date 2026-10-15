"""Tests one enemy drawn to the hunter: lent the zone, the hunter imposed, then its brain's walk when far, each call
announced first with its name; near, no walk; a zone not taken or a failing call says why and stops there; lost when
gone, dead (as reads.dead says it), in the reserve or given another zone; kept on the hunter: the walk aborted within
ARRIVAL_M, given again past REWALK_M, given again while still farther than ARRIVAL_M once the game ended it and
REWALK_EVERY_S has passed (an unreadable Exec counts as running), the hunter imposed again once the game cleared the
target when asked (never over another script's, a refusal only said); released once, nothing called on a body the game
reuses. The walks run through the real brain_walk: an ended walk's block is taken over by the next walk, a running
one's never, and a chaser whose ended walk's block another chaser took still reads its walk ended and is walked
again on time."""

import inspect
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
from sdk_stubs import FakeWeak  # noqa: E402

state = sdk_stubs.install()

import chaser_fixture  # noqa: E402
from chaser_fixture import character  # noqa: E402

game = chaser_fixture.Game(state)

from it_follows import brain_walk, chaser as chasers  # noqa: E402
from it_follows.seen import Seen  # noqa: E402

brain_walk.process_event = lambda: game.process_event
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


behaviour = {"take": "target", "lend_fails": False}
# Each announce: (call, whether it goes to the SDK log, again).
announced: list[tuple] = []


class Zone:
    """Stands for hunter_zone.HunterZone: zones are named lent, own or other."""

    def lend(self, seen: object) -> str:
        game.log.append(("lend", seen.name))
        if behaviour["lend_fails"]:
            raise RuntimeError("refused")
        return behaviour["take"]

    def held(self, name: str, zone: object) -> str:
        return "none" if zone is None else "target" if zone == "lent" else zone

    def give_back(self, name: str, actor: object, body_reused: bool) -> str:
        game.log.append(("give_back", name, body_reused))
        return "not_needed" if body_reused else "restored"


def announce(call: str, **fields: object) -> None:
    game.log.append(("announce", call, fields.get("on")))
    announced.append((call, fields.get("log", True), fields.get("again")))


hunter, pc, zone = character(1), object(), Zone()


def fresh(address: int = 20, walks: bool = True, keep_blocks: bool = False) -> tuple:
    """A new enemy and its chaser, with a fresh game; the walks' blocks forgotten unless keep_blocks."""
    game.reset()
    announced.clear()
    behaviour.update(take="target", lend_fails=False)
    if not keep_blocks:
        sys.modules.pop(brain_walk.KEPT_MODULE, None)
    enemy = character(address)
    enemy.zone = "lent"
    enemy.GetTerritory = lambda: enemy.zone
    seen = Seen(actor=enemy, name=f"cat_{address}", definition="Char_CatAdult", zone=None, zone_path="",
                centre=None, radius_m=30.0, at=None, walks=walks)
    return chasers.Chaser(seen, FakeWeak(hunter), announce), seen, enemy


try:
    check("a chaser is made of what the census saw, the hunter's weak pointer and announce",
          list(inspect.signature(chasers.Chaser).parameters) == ["seen", "player_ref", "announce"])
    check("the thresholds of the trials", (chasers.ARRIVAL_M, chasers.REWALK_M, chasers.REWALK_EVERY_S)
          == (35.0, 75.0, 5.0))

    chaser, seen, enemy = fresh()
    refused = chaser.draw(zone, seen, hunter, pc, True, 0.0)
    check("a far enemy is lent the zone, the hunter imposed, then walked to him, each call announced first, named",
          refused is None and chaser.state == "walking" and chaser.outcome() == "0"
          and game.log == [("lend", "cat_20"), ("announce", "AISetScriptedTarget", "cat_20"),
                           ("set", enemy, hunter, False), ("announce", "AIScriptedMove", "cat_20"),
                           ("walk", enemy, hunter)] and chaser.patch.read() == "player")
    check("its first walk is written to the log, said not to be given again",
          ("AIScriptedMove", True, False) in announced)
    check("held in the lent zone, it is not lost", chaser.check(zone) == (enemy, None))
    check("its kind is the one read by the census", chaser.kind == "Char_CatAdult" and chaser.name == "cat_20")
    game.log.clear()
    check("kept far, it walks on", chaser.keep(36.0, hunter, pc, True, 1.0) == {} and chaser.state == "walking"
          and game.log == [])
    check("within ARRIVAL_M its walk is aborted, announced first",
          chaser.keep(35.0, hunter, pc, True, 1.0) == {"walk": "aborted"} and chaser.state == "arrived"
          and game.log == [("announce", "AbortScriptedBrainTask", "cat_20"), ("abort", enemy, True)])
    game.log.clear()
    check("arrived, it is left alone up to REWALK_M", chaser.keep(10.0, hunter, pc, True, 1.0) == {}
          and chaser.keep(75.0, hunter, pc, True, 1.0) == {} and game.log == [])
    announced.clear()
    check("past REWALK_M it is walked again, announced first", chaser.keep(75.1, hunter, pc, True, 1.0)
          == {"walk": "again"} and chaser.state == "walking"
          and game.log == [("announce", "AIScriptedMove", "cat_20"), ("walk", enemy, hunter)]
          and announced == [("AIScriptedMove", True, True)])
    check("and aborted again once back", chaser.keep(20.0, hunter, pc, True, 1.0) == {"walk": "aborted"})
    check("without its distance nothing is decided", chaser.keep(None, hunter, pc, True, 1.0) == {})
    game.imposed.clear()
    game.log.clear()
    announced.clear()
    check("a target the game cleared is imposed again, announced but not written to the log",
          chaser.keep(20.0, hunter, pc, True, 1.0) == {"target": "again"} and chaser.patch.read() == "player"
          and game.log == [("announce", "AISetScriptedTarget", "cat_20"), ("set", enemy, hunter, False)]
          and announced == [("AISetScriptedTarget", False, True)])
    game.imposed.clear()
    game.log.clear()
    check("without impose_again, a target the game cleared stays cleared", chaser.keep(20.0, hunter, pc, False, 1.0)
          == {} and chaser.patch.read() == "none" and game.log == [])
    other_script = character(99)
    game.imposed[20] = other_script
    game.log.clear()
    check("never over another script's target", chaser.keep(20.0, hunter, pc, True, 1.0) == {}
          and game.imposed[20] is other_script and game.log == [])
    game.imposed[20] = hunter
    game.log.clear()
    released = chaser.release(zone, "chased", False)
    check("released: its own zone given back, the target cleared, announced first",
          released == {"order": "inactive", "restoration": "restored", "target": "restored"}
          and chaser.ended == "chased"
          and game.log == [("give_back", "cat_20", False), ("announce", "AIClearScriptedTarget", "cat_20"),
                           ("clear", enemy)])
    check("only once", chaser.release(zone, "manual", False) == {} and chaser.ended == "chased")

    chaser, seen, enemy = fresh()
    check("a near enemy is not walked", chaser.draw(zone, seen, hunter, pc, False, 0.0) is None
          and chaser.state == "near" and not any(step[0] == "walk" for step in game.log)
          and chaser.patch.read() == "player" and chaser.outcome() is None)

    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, True, 0.0)
    game.log.clear()
    check("released while walking, the walk is aborted first", chaser.release(zone, "manual", False)["order"]
          == "aborted" and game.log[:2] == [("announce", "AbortScriptedBrainTask", "cat_20"), ("abort", enemy, True)])

    for label, setup, reason in (
            ("gone", lambda enemy: setattr(enemy, "freed", True), "mover_gone"),
            ("dead", lambda enemy: setattr(enemy.HealthState, "bCurrentlyDead", True), "mover_dead"),
            ("in the reserve, without a zone", lambda enemy: setattr(enemy, "zone", None), "mover_parked"),
            ("given another zone by the game", lambda enemy: setattr(enemy, "zone", "other"), "zone_changed_by_game"),
            ("holding its own zone again", lambda enemy: setattr(enemy, "zone", "own"), "zone_changed_by_game")):
        chaser, seen, enemy = fresh()
        chaser.draw(zone, seen, hunter, pc, True, 0.0)
        setup(enemy)
        check(f"an enemy {label} is lost", chaser.check(zone)[1] == reason)
    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, True, 0.0)
    held = chaser.check(zone)
    enemy.freed = True
    check("a gone enemy is given back as none", held == (enemy, None) and chaser.check(zone) == (None, "mover_gone"))
    for label, health in (("a death the game does not say with a bool", types.SimpleNamespace(bCurrentlyDead=1)),
                          ("a health it cannot read", None)):
        chaser, seen, enemy = fresh()
        chaser.draw(zone, seen, hunter, pc, False, 0.0)
        enemy.HealthState = health
        check(f"as reads.dead says it, {label} does not lose the enemy", chaser.check(zone) == (enemy, None))

    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, True, 0.0)
    enemy.HealthState.bCurrentlyDead = True
    game.log.clear()
    check("on a body the game reuses nothing is called, the zone told so",
          chaser.release(zone, "mover_dead", True) == {"order": "not_needed", "restoration": "not_needed",
                                                         "target": "not_needed"}
          and game.log == [("give_back", "cat_20", True)])

    chaser, seen, enemy = fresh()
    behaviour["take"] = "own"
    check("a zone not taken stops there, before any target",
          chaser.draw(zone, seen, hunter, pc, True, 0.0) == "zone_not_taken" and game.log == [("lend", "cat_20")])
    chaser, seen, enemy = fresh()
    behaviour["lend_fails"] = True
    check("a failing lend says so", chaser.draw(zone, seen, hunter, pc, True, 0.0) == "zone_call_failed:RuntimeError"
          and game.log == [("lend", "cat_20")])
    chaser, seen, enemy = fresh()
    game.set_fails = "before"
    check("a failing target says so, before any walk",
          chaser.draw(zone, seen, hunter, pc, True, 0.0) == "target_not_taken:RuntimeError"
          and not any(step[0] == "walk" for step in game.log))
    chaser, seen, enemy = fresh()
    game.walk_fails = TypeError("refused")
    refused = chaser.draw(zone, seen, hunter, pc, True, 0.0)
    game.log.clear()
    check("a failing walk says so, and is aborted all the same at the release",
          refused == "order_not_taken:TypeError" and chaser.release(zone, refused, False)["order"] == "aborted"
          and ("abort", enemy, True) in game.log)

    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, False, 0.0)
    check("a near enemy is walked once the hunter has gone past REWALK_M",
          chaser.keep(80.0, hunter, pc, True, 1.0) == {"walk": "again"} and chaser.state == "walking")
    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, False, 0.0)
    game.imposed.clear()
    game.set_fails = "before"
    check("a refused target is only said, the enemy kept, and tried again at the next sample",
          chaser.keep(20.0, hunter, pc, True, 1.0) == {"target": "refused:RuntimeError"} and chaser.ended is None
          and chaser.keep(20.0, hunter, pc, True, 1.0) == {"target": "refused:RuntimeError"})
    game.set_fails = None
    check("then taken", chaser.keep(20.0, hunter, pc, True, 1.0) == {"target": "again"}
          and chaser.patch.read() == "player")
    game.walk_fails = TypeError("refused")
    try:
        chaser.keep(80.0, hunter, pc, True, 1.0)
        raised = False
    except TypeError:
        raised = True
    game.walk_fails = None
    game.log.clear()
    check("a failing walk given again raises, and is aborted all the same at the release",
          raised and chaser.release(zone, "walk_again_failed:TypeError", False)["order"] == "aborted"
          and ("abort", enemy, True) in game.log)

    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, True, 100.0)
    chaser.block.block.Exec = 2
    ended_walk = chaser.block
    game.log.clear()
    check("a walk the game ended is not given again before REWALK_EVERY_S since the last one, nor without a distance",
          chaser.keep(150.0, hunter, pc, False, 100.0 + chasers.REWALK_EVERY_S - 0.1) == {}
          and chaser.keep(None, hunter, pc, False, 400.0) == {} and game.log == [])
    check("then, still farther than ARRIVAL_M, it is given again, announced first, its ended block taken over",
          chaser.keep(36.0, hunter, pc, False, 100.0 + chasers.REWALK_EVERY_S) == {"walk": "again_after_end"}
          and game.log == [("announce", "AIScriptedMove", "cat_20"), ("walk", enemy, hunter)]
          and chaser.block is not ended_walk and chaser.block.block is ended_walk.block
          and len(brain_walk.kept()) == 1 and chaser.outcome() == "0" and chaser.state == "walking")
    check("the walk it ended still reads ended, with what the game wrote", brain_walk.ended(ended_walk)
          and brain_walk.outcome(ended_walk) == "2")
    game.log.clear()
    check("while the new walk runs, nothing more is given", chaser.keep(150.0, hunter, pc, False, 200.0) == {}
          and game.log == [])
    chaser.block.block.Exec = 2
    check("ended within ARRIVAL_M, it has arrived: aborted, not given again",
          chaser.keep(35.0, hunter, pc, False, 200.0) == {"walk": "aborted"} and chaser.state == "arrived"
          and not any(step[0] == "walk" for step in game.log))
    chaser, seen, enemy = fresh()
    chaser.draw(zone, seen, hunter, pc, True, 100.0)
    chaser.block = types.SimpleNamespace()
    game.log.clear()
    check("a walk whose Exec cannot be read is never given again", chaser.keep(150.0, hunter, pc, False, 300.0) == {}
          and game.log == [] and chaser.outcome() == "unreadable:AttributeError")

    first, first_seen, first_enemy = fresh(40)
    first.draw(zone, first_seen, hunter, pc, True, 100.0)
    second, second_seen, second_enemy = fresh(41, keep_blocks=True)
    second.draw(zone, second_seen, hunter, pc, True, 100.0)
    check("a running walk's block is never taken by another chaser's walk",
          second.block.block is not first.block.block and len(brain_walk.kept()) == 2
          and first.block.block.AIActor is first_enemy and not brain_walk.ended(first.block))
    first.block.block.Exec = 2
    third, third_seen, third_enemy = fresh(42, keep_blocks=True)
    third.draw(zone, third_seen, hunter, pc, True, 101.0)
    check("an ended one's is: another chaser's walk takes it over",
          third.block.block is first.block.block and len(brain_walk.kept()) == 2
          and first.block.block.AIActor is third_enemy and first.block.block.Exec == brain_walk.START)
    game.log.clear()
    check("the chaser whose ended walk's block was taken still reads its walk ended",
          first.outcome() == "2" and first.keep(150.0, hunter, pc, False, 100.0 + chasers.REWALK_EVERY_S - 0.1)
          == {} and game.log == [])
    check("and is walked again on time, in a block of its own, the other chaser's walk left running",
          first.keep(150.0, hunter, pc, False, 100.0 + chasers.REWALK_EVERY_S) == {"walk": "again_after_end"}
          and first.block.block not in (third.block.block, second.block.block) and len(brain_walk.kept()) == 3
          and game.log[-1] == ("walk", first_enemy, hunter) and not brain_walk.ended(third.block)
          and third.block.block.AIActor is third_enemy)

    flyer, seen, enemy = fresh(30, walks=False)
    refused = flyer.draw(zone, seen, hunter, pc, True, 0.0)
    check("trial 6r: a flyer far away is lent the zone and the hunter imposed, never told to walk",
          refused is None and flyer.state == "flying" and flyer.patch.read() == "player"
          and game.log == [("lend", "cat_30"), ("announce", "AISetScriptedTarget", "cat_30"),
                           ("set", enemy, hunter, False)])
    game.log.clear()
    check("nor later, however far, and its release has no walk to abort",
          flyer.keep(500.0, hunter, pc, True, 50.0) == {} and flyer.keep(10.0, hunter, pc, True, 60.0) == {}
          and game.log == [] and flyer.release(zone, "mover_dead", False)["order"] == "inactive")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
