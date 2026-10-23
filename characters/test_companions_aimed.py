"""Tests the Vault Hunter aimed at (companions/aimed.py): the camera's direction from its pitch and yaw; the nearest
place along the camera's line within REACH_CM of it, none behind the camera or past FARTHEST_CM; read from the
player's camera, the hunters only, each by its name shown, an actor gone left out; kept HOLD_S after the line leaves
it, another one replacing it at once; no player, no one; a camera that cannot be read, no one, said once."""

import json
import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from characters.companions import aimed  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Characters] ")) for text in state["info"]
             if text.startswith("[Characters] {")]
    return [line for line in found if line["event"] == event]


def ns(**fields: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**fields)


def close(a: tuple, b: tuple) -> bool:
    return all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


check("a body's middle within 80 cm of the line, 150 m at most, kept 1 s", aimed.REACH_CM == 80.0
      and aimed.FARTHEST_CM == 15000.0 and aimed.HOLD_S == 1.0)
check("the camera's direction: ahead, to the side, up", close(aimed.facing(ns(Pitch=0.0, Yaw=0.0)), (1, 0, 0))
      and close(aimed.facing(ns(Pitch=0.0, Yaw=90.0)), (0, 1, 0))
      and close(aimed.facing(ns(Pitch=90.0, Yaw=30.0)), (0, 0, 1)))

EYE, AHEAD = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)
check("one on the line: it", aimed.nearest(EYE, AHEAD, [("Vex", (1000.0, 50.0, 0.0))]) == "Vex")
check("two on the line: the nearer", aimed.nearest(EYE, AHEAD, [("Vex", (1000.0, 0.0, 0.0)),
                                                                 ("Rafa", (500.0, 0.0, 70.0))]) == "Rafa")
check("at REACH_CM exactly: it; just past: none", aimed.nearest(EYE, AHEAD, [("Vex", (1000.0, 0.0, 80.0))]) == "Vex"
      and aimed.nearest(EYE, AHEAD, [("Vex", (1000.0, 0.0, 80.5))]) is None)
check("behind the camera, past FARTHEST_CM, nothing: none", aimed.nearest(EYE, AHEAD, [
      ("Vex", (-500.0, 0.0, 0.0)), ("Rafa", (15001.0, 0.0, 0.0))]) is None and aimed.nearest(EYE, AHEAD, []) is None)


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def spot(x: float, y: float, z: float) -> types.SimpleNamespace:
    return ns(X=x, Y=y, Z=z)


def companion(name: str, where: tuple | None) -> types.SimpleNamespace:
    actor = None if where is None else ns(K2_GetActorLocation=lambda: spot(*where))
    return ns(companion=name, actor=lambda: actor)


camera = {"turn": ns(Pitch=0.0, Yaw=0.0), "fails": None}


def rotation() -> types.SimpleNamespace:
    if camera["fails"] is not None:
        raise camera["fails"]
    return camera["turn"]


PC = ns(PlayerCameraManager=ns(GetCameraLocation=lambda: spot(0.0, 0.0, 0.0), GetCameraRotation=rotation))
NAMES = {"Crankus": "Crankus", "Vex": "VEX SHOWN"}
crew = [companion("Crankus", (300.0, 0.0, 0.0)), companion("Vex", (1000.0, 0.0, 0.0)), companion("Rafa", None),
        companion("Amon", (0.0, 1000.0, 0.0))]
clock = Clock()
looking = aimed.Aimed(clock)
check("the hunter on the camera's line, by its name shown; the ally nearer left out; a body gone left out",
      looking.look(PC, crew, NAMES) == "VEX SHOWN")
camera["turn"] = ns(Pitch=0.0, Yaw=90.0)
check("turned to another hunter: him at once, by his own name when none is shown",
      looking.look(PC, crew, NAMES) == "Amon")
camera["turn"] = ns(Pitch=90.0, Yaw=0.0)
clock.now += 0.9
check("the line off every hunter: the last one kept HOLD_S", looking.look(PC, crew, NAMES) == "Amon")
clock.now += 0.1
check("then no one", looking.look(PC, crew, NAMES) is None and looking.look(PC, crew, NAMES) is None)
camera["turn"] = ns(Pitch=0.0, Yaw=0.0)
state["info"].clear()
check("no player: no one, nothing said", aimed.Aimed(clock).look(None, crew, NAMES) is None
      and notes("companion_aim_failed") == [])
camera["fails"] = RuntimeError("no camera")
failing = aimed.Aimed(clock)
state["info"].clear()
check("a camera that cannot be read: no one, said once", failing.look(PC, crew, NAMES) is None
      and failing.look(PC, crew, NAMES) is None and notes("companion_aim_failed") == [
          {"event": "companion_aim_failed", "run": 0, "why": "RuntimeError:no camera"}])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
