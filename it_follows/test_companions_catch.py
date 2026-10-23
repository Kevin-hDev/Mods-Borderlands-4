"""Tests the catch-up (catch.py), since trial 166 the rule of Vex Phase Clones and Loveless Wyrms: no teleport
within TELEPORT_M; beyond it, the companion teleported BEHIND_M behind the hunter, where he faces away, at his height,
facing him, said first; one SPREAD_DEG rank each, behind or beside him, never in front, no two ranks on one spot; at
most every EVERY_S; nothing while he is in the air, climbing, swimming or his mode unread, the companion teleported
once he lands; nothing when where he faces cannot be read; a refusal counted, an answer in a tuple read as Vex reads
it. Trial 166's case: the hunter crossing 100 m in the air or unread then standing still, the companion brought to
him, never back to where it started. Since trial 168, as Vex's Specters: never while the companion fights, however
far, until trial 169: fighting, teleported beyond FIGHT_TELEPORT_M (100 m); unstick teleports it to its place behind
him near or far, on the same conditions (ground, facing, EVERY_S), and says no_hunter without him."""

import math
import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct=name, **fields)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_catch_under_test", HERE / "it_follows" / "companions" / "catch.py")
catch_module = util.module_from_spec(spec)
spec.loader.exec_module(catch_module)

events: list[str] = []
FOOT = "MOVE_Walking"


class Companion:
    def __init__(self) -> None:
        self.answer: object = True
        self.asked: list = []

    def K2_TeleportTo(self, DestLocation: object, DestRotation: object) -> object:
        events.append("teleport")
        self.asked.append((DestLocation, DestRotation))
        return self.answer


def catch(rank: int = 0) -> tuple:
    events.clear()
    companion = Companion()
    return catch_module.CatchUp(lambda: companion, "Frame_1", lambda text: events.append(f"note {text}"), rank), \
        companion


def landed(companion: Companion) -> tuple:
    where = companion.asked[-1][0]
    return where.X, where.Y, where.Z


def near(a: tuple, b: tuple) -> bool:
    return math.dist(a, b) < 1e-6


check("10 m behind since trial 167, eight ranks behind or beside", catch_module.TELEPORT_M == 50.0
      and catch_module.BEHIND_M == 10.0 and catch_module.SPREAD_DEG == 22.5 and catch_module.EVERY_S == 5.0)
here = (10000.0, 0.0, 300.0)
catcher, companion = catch()
check("within TELEPORT_M: nothing called", catcher.keep(here, 0.0, FOOT, 50.0, 0.0) == "near" and events == [])
check("no distance or no hunter: nothing called", catcher.keep(here, 0.0, FOOT, None, 0.0) == "near"
      and catcher.keep(None, 0.0, FOOT, 90.0, 0.0) == "near" and events == [])
check("beyond it: teleported, said first", catcher.keep(here, 0.0, FOOT, 50.1, 1.0) == "teleported"
      and events == ["note about to call K2_TeleportTo on Frame_1", "teleport"] and catcher.teleports == 1)
check("BEHIND_M behind him where he faces away, at his height", near(landed(companion), (9000.0, 0.0, 300.0)))
check("facing him", math.isclose(companion.asked[0][1].Yaw, 0.0, abs_tol=1e-9) and companion.asked[0][1].Pitch == 0.0)
check("not again within EVERY_S", catcher.keep(here, 0.0, FOOT, 80.0, 5.9) == "waiting" and len(companion.asked) == 1)
companion.answer = False
check("again after EVERY_S; a refusal counted", catcher.keep(here, 0.0, FOOT, 80.0, 6.0) == "refused"
      and catcher.refused == 1 and catcher.teleports == 2)
companion.answer = (False,)
check("an answer in a tuple read as Vex reads it", catcher.keep(here, 0.0, FOOT, 80.0, 11.0) == "refused"
      and catcher.refused == 2)
companion.answer = (True,)
check("and done when it says so", catcher.keep(here, 0.0, FOOT, 80.0, 16.0) == "teleported" and catcher.refused == 2)

catcher, companion = catch()
catcher.keep((0.0, 0.0, 0.0), 90.0, FOOT, 60.0, 0.0)
check("behind where he faces, whatever way that is", near(landed(companion), (0.0, -1000.0, 0.0))
      and math.isclose(companion.asked[0][1].Yaw, 90.0))

for mode in ("MOVE_Falling", "MOVE_Custom", "MOVE_Swimming", "MOVE_Flying", None):
    catcher, companion = catch()
    check(f"{mode}: nothing called, it waits for him to land",
          catcher.keep(here, 0.0, mode, 90.0, 0.0) == "waits_landing" and events == [] and catcher.at is None)
for mode in ("MOVE_None", "MOVE_NavWalking"):
    catcher, companion = catch()
    check(f"{mode} (driving, or on the game's walking map): teleported",
          catcher.keep(here, 0.0, mode, 90.0, 0.0) == "teleported")
catcher, companion = catch()
check("where he faces unread: nothing called", catcher.keep(here, None, FOOT, 90.0, 0.0) == "no_facing"
      and events == [] and catcher.at is None)
catcher, companion = catch()
check("fighting within FIGHT_TELEPORT_M: nothing called", catch_module.FIGHT_TELEPORT_M == 100.0
      and catcher.keep(here, 0.0, FOOT, 100.0, 0.0, True) == "fighting" and events == [] and catcher.at is None)
check("fighting beyond it: teleported behind him all the same", catcher.keep(here, 0.0, FOOT, 100.1, 0.0, True)
      == "teleported" and near(landed(companion), catch_module.behind(here, 0.0, 0)))
catcher, companion = catch()
check("near and fighting: near", catcher.keep(here, 0.0, FOOT, 10.0, 0.0, True) == "near")
catcher, companion = catch(2)
check("unstick: teleported to its place behind him, however near", catcher.unstick(here, 0.0, FOOT, 0.0)
      == "teleported" and near(landed(companion), catch_module.behind(here, 0.0, 2)) and catcher.teleports == 1)
check("unstick: not again within EVERY_S", catcher.unstick(here, 0.0, FOOT, 4.9) == "waiting")
catcher, companion = catch()
check("unstick: him in the air, it waits", catcher.unstick(here, 0.0, "MOVE_Falling", 0.0) == "waits_landing"
      and events == [])
check("unstick: no hunter", catcher.unstick(None, 0.0, FOOT, 0.0) == "no_hunter" and events == [])

catcher, companion = catch()
start = (0.0, 0.0, 0.0)
for second, x, mode in ((0, 4500.0, FOOT), (1, 6000.0, None), (2, 8000.0, "MOVE_Falling"), (3, 10000.0, None),
                        (4, 12000.0, FOOT)):
    catcher.keep((x, 0.0, 0.0), 0.0, mode, x / 100.0, float(second))
check("trial 166: the hunter crossing 100 m in the air or unread, nothing until he stands", len(companion.asked) == 1)
check("then the companion brought to him, never back where it started",
      near(landed(companion), (11000.0, 0.0, 0.0)) and math.dist(landed(companion), start) > 10000.0)
for second in range(5, 60):
    catcher.keep((12000.0, 0.0, 0.0), 0.0, FOOT, 4.0, float(second))
check("there it is near: no teleport again", len(companion.asked) == 1)

spots = []
for rank in range(8):
    catcher, companion = catch(rank)
    catcher.keep((0.0, 0.0, 0.0), 0.0, FOOT, 90.0, 0.0)
    spots.append(landed(companion))
check("eight ranks, eight spots", len({(round(x), round(y)) for x, y, _ in spots}) == 8)
check("each BEHIND_M from him", all(math.isclose(math.hypot(x, y), 1000.0) for x, y, _ in spots))
check("behind him or beside him, never in front", all(x <= 1e-6 for x, _, _ in spots))
check("at least 3.8 m apart", min(math.dist(a, b) for a in spots for b in spots if a is not b) > 380.0)
check("rank 0 right behind, then one each way", catch_module.fan(0) == 0.0 and catch_module.fan(1) == 22.5
      and catch_module.fan(2) == -22.5 and catch_module.fan(7) == 90.0)


class Facing:
    def __init__(self, yaw: object) -> None:
        self.yaw = yaw

    def K2_GetActorRotation(self) -> object:
        if isinstance(self.yaw, Exception):
            raise self.yaw
        return types.SimpleNamespace(Yaw=self.yaw)


check("where he faces read", catch_module.facing(Facing(37.5)) == 37.5)
check("unreadable or not a number: None", catch_module.facing(Facing(RuntimeError("gone"))) is None
      and catch_module.facing(Facing(float("nan"))) is None and catch_module.facing(None) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
