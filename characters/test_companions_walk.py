"""Tests trial 136's walk (walk.py): nothing without the hunter's distance or the hunter; no walk within WALK_M;
a walk beyond it, said before it is made, one at a time; given again once the game ended it, not before
REWALK_EVERY_S; aborted within ARRIVAL_M, said first; since trial 166 farther (WALK_M 15, ARRIVAL_M 10) and asked
between samples too (arrive): aborted within ARRIVAL_M, nothing beyond it or without a walk or a distance; a failing
walk counted, so that it is aborted; the stop said for each case; since trial 168 (push.py, the real one):
within PUSH_M, pushed to its place on its own side turned by its rank's step instead of the game's walk, which is
turned into a push once within PUSH_M; a push stepped between samples toward the ARRIVAL_M circle, stopped there with
nothing called; live while pushed or while the game's walk runs; without places, the game's walk; then It Follows' own
walk module, loaded from its file, at the boundary: its functions and its abort."""

import inspect
import math
import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_walk_under_test", HERE / "characters" / "companions" / "walk.py")
walking = util.module_from_spec(spec)
spec.loader.exec_module(walking)
push_spec = util.spec_from_file_location("follow_push_for_walk", HERE / "characters" / "companions" / "push.py")
pushing = util.module_from_spec(push_spec)
push_spec.loader.exec_module(pushing)
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct=name, **fields)

events: list[str] = []


class Brain:
    def __init__(self) -> None:
        self.fail_walk = self.fail_abort = False

    def walk(self, actor: object, goal: object, pc: object) -> object:
        events.append(f"walk {actor} {goal} {pc}")
        if self.fail_walk:
            raise RuntimeError("refused")
        return types.SimpleNamespace(Exec=0)

    def ended(self, block: object) -> bool:
        return block.Exec != 0

    def outcome(self, block: object) -> str:
        return f"Exec {block.Exec}"

    def abort(self, actor: object) -> None:
        events.append(f"abort {actor}")
        if self.fail_abort:
            raise RuntimeError("refused")


class Companion:
    """A companion the push moves: each push recorded."""

    def __init__(self) -> None:
        self.inputs: list = []

    def __str__(self) -> str:
        return "lemmy"

    def AddMovementInput(self, WorldDirection: object, ScaleValue: float, bForce: bool) -> None:
        events.append("pushed")
        self.inputs.append(WorldDirection)


def walker(actor: object = "lemmy", turn: float = 0.0) -> tuple:
    events.clear()
    brain = Brain()
    note = lambda text: events.append(f"note {text}")  # noqa: E731
    return walking.Walker(lambda: actor, "Lemmy_1", note, brain, pushing.Push(lambda: actor, "Lemmy_1", note),
                          turn), brain


check("the distances of trial 166", walking.WALK_M == 15.0 and walking.ARRIVAL_M == 10.0
      and walking.PUSH_M == 20.0
      and walking.ARRIVAL_EVERY_S == 0.2)
walker_, brain = walker()
check("nothing without a distance or the hunter", walker_.keep(None, "hunter", "pc", 0.0) == "unknown"
      and walker_.keep(30.0, None, "pc", 0.0) == "unknown" and events == [])
check("no walk within WALK_M", walker_.keep(15.0, "hunter", "pc", 0.0) == "near" and events == [])
check("close, not walking: nothing to abort", walker_.keep(3.0, "hunter", "pc", 0.0) == "near" and events == [])
check("no outcome before a walk", walker_.outcome() is None)
check("a walk beyond WALK_M, said first", walker_.keep(15.1, "hunter", "pc", 1.0) == "walk" and events == [
      "note about to call AIScriptedMove on Lemmy_1", "walk lemmy hunter pc"] and walker_.walks == 1)
check("one walk at a time", walker_.keep(40.0, "hunter", "pc", 2.0) == "walking" and walker_.walks == 1)
check("a walk still running not given again, however long", walker_.keep(40.0, "hunter", "pc", 30.0) == "walking"
      and walker_.walks == 1)
walker_.block.Exec = 2
check("ended by the game: not given again before REWALK_EVERY_S", walker_.keep(40.0, "hunter", "pc", 5.9)
      == "walking" and walker_.walks == 1)
check("given again once REWALK_EVERY_S has gone", walker_.keep(40.0, "hunter", "pc", 6.0) == "walk_again"
      and walker_.walks == 2 and walker_.walked_at == 6.0)
check("its outcome read", (setattr(walker_.block, "Exec", 1), walker_.outcome())[1] == "Exec 1")
walker_.block.Exec = 0
events.clear()
check("not aborted beyond ARRIVAL_M, between samples", walker_.arrive(10.1) is None and walker_.walking
      and walker_.arrive(None) is None and walker_.walking and events == [])
check("aborted within ARRIVAL_M, said first", walker_.keep(10.0, "hunter", "pc", 7.0) == "arrived:aborted"
      and events == ["note about to call AbortScriptedBrainTask on Lemmy_1", "abort lemmy"]
      and not walker_.walking)
check("arrived: no walk while within WALK_M", walker_.keep(14.0, "hunter", "pc", 20.0) == "near")
check("no walk: nothing to arrive from", walker_.arrive(1.0) is None)
walker_.keep(40.0, "hunter", "pc", 21.0)
events.clear()
check("between samples: aborted within ARRIVAL_M, said first", walker_.arrive(9.9) == "arrived:aborted"
      and events == ["note about to call AbortScriptedBrainTask on Lemmy_1", "abort lemmy"] and not walker_.walking)
check("the stop of a walker not walking: inactive", walker_.stop() == "inactive")

walker_, brain = walker()
brain.fail_walk = True
try:
    walker_.keep(30.0, "hunter", "pc", 0.0)
    raised = False
except RuntimeError:
    raised = True
check("a failing walk raises, counted as walking", raised and walker_.walking)
check("so that it is aborted", walker_.stop() == "aborted" and events[-1] == "abort lemmy")

walker_, brain = walker(None)
walker_.walking = True
check("the character gone: unavailable", walker_.stop() == "unavailable" and events == [])
walker_, brain = walker()
walker_.walking, brain.fail_abort = True, True
check("a failing abort said", walker_.stop() == "abort_error:RuntimeError" and not walker_.walking)

hunter_at = (0.0, 0.0, 0.0)
companion = Companion()
walker_, brain = walker(companion, 22.5)
check("within PUSH_M, beyond WALK_M: pushed to its place, no walk of the game", walker_.keep(
      18.0, "hunter", "pc", 0.0, hunter_at, (-1800.0, 0.0, 0.0)) == "push" and walker_.walking
      and walker_.push.active and abs(walker_.push.aim - 202.5) < 1e-9 and walker_.walks == 0 and walker_.pushed == 1
      and events == [])
check("pushed: live, the next sample says so", walker_.live()
      and walker_.keep(17.0, "hunter", "pc", 1.0, hunter_at, (-1700.0, 0.0, 0.0)) == "pushing")
place = pushing.spot(hunter_at, 202.5, walking.ARRIVAL_M)
towards = (place[0] + 1700.0, place[1])
check("between samples, a push toward its place on the ARRIVAL_M circle", walker_.step(
      hunter_at, (-1700.0, 0.0, 0.0), 17.0) is None and len(companion.inputs) == 1
      and abs(companion.inputs[0].X - towards[0] / math.hypot(*towards)) < 1e-9
      and abs(companion.inputs[0].Y - towards[1] / math.hypot(*towards)) < 1e-9
      and events[0].startswith("note about to call AddMovementInput on Lemmy_1"))
check("no step without places", walker_.step(None, (-1700.0, 0.0, 0.0), 17.0) is None and len(companion.inputs) == 1)
events.clear()
check("within ARRIVAL_M: the push stopped, nothing called", walker_.step(hunter_at, (-990.0, 0.0, 0.0), 9.9)
      == "arrived:pushed" and not walker_.walking and not walker_.push.active and events == []
      and len(companion.inputs) == 1 and not walker_.live())
check("not pushed: no step", walker_.step(hunter_at, (-990.0, 0.0, 0.0), 9.9) is None)
walker_, brain = walker(companion)
check("beyond PUSH_M: the game's walk", walker_.keep(25.0, "hunter", "pc", 0.0, hunter_at, (-2500.0, 0.0, 0.0))
      == "walk" and walker_.walks == 1 and not walker_.push.active and walker_.live())
check("its walk ended by the game: no longer live", (setattr(walker_.block, "Exec", 2), walker_.live())[1] is False)
walker_.block.Exec = 0
events.clear()
check("then within PUSH_M: the game's walk aborted, said first, and a push begun",
      walker_.keep(19.0, "hunter", "pc", 1.0, hunter_at, (-1900.0, 0.0, 0.0)) == "push:aborted"
      and events == ["note about to call AbortScriptedBrainTask on Lemmy_1", "abort lemmy"]
      and walker_.walking and walker_.push.active and walker_.pushed == 1)
check("stopped while pushed: nothing called", (events.clear(), walker_.stop())[1] == "pushed" and events == []
      and not walker_.walking and not walker_.push.active)
walker_, brain = walker(companion)
check("at PUSH_M itself: pushed", walker_.keep(20.0, "hunter", "pc", 0.0, hunter_at, (-2000.0, 0.0, 0.0)) == "push")
walker_, brain = walker(companion)
check("within PUSH_M without places: the game's walk", walker_.keep(18.0, "hunter", "pc", 0.0) == "walk"
      and walker_.walks == 1)
check("not walking: not live", not walker(companion)[0].live())

aborted: list[dict] = []
state["classes"]["GbxBrainFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    AbortScriptedBrainTask=lambda **kwargs: aborted.append(kwargs)))
from characters import brain_walk as real  # noqa: E402

check("It Follows' walk module, as the follow hands it", all(callable(getattr(real, name, None))
                                                              for name in ("walk", "ended", "outcome", "abort"))
      and list(inspect.signature(real.walk).parameters) == ["actor", "goal", "pc"])
check("its ended read as the walker reads it", real.ended(types.SimpleNamespace(Exec=0)) is False
      and real.ended(types.SimpleNamespace(Exec=2)) is True)
walker_ = walking.Walker(lambda: "lemmy", "Lemmy_1", lambda text: None, real,
                         pushing.Push(lambda: "lemmy", "Lemmy_1", lambda text: None))
walker_.walking = True
check("its abort called as the game takes it", walker_.stop() == "aborted"
      and aborted == [{"AIActor": "lemmy", "bStopImmediately": True}])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
