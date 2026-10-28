"""Tests where the world must hold a spot for it to show where the first-person arms show it."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import arms_view, report  # noqa: E402

fails: list[str] = []
# The game's own numbers: the arms at 77 degrees, Kevin's world at 110.
SPREAD = math.tan(math.radians(110.0) / 2) / math.tan(math.radians(77.0) / 2)
PALM = (40.0, -25.0, 30.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


def on_screen(spot, eye, angle):
    """Where a spot ahead of a camera looking along X shows, as fractions of the half screen."""
    ahead, right, up = spot[0] - eye[0], spot[1] - eye[1], spot[2] - eye[2]
    half = math.tan(math.radians(angle) / 2)
    return right / ahead / half, up / ahead / half


pc, _character = sdk_stubs.player(state)
camera = pc.PlayerCameraManager
EYE = (0.0, 0.0, 50.0)

check("with the arms drawn as the world is, a spot stays where it is", arms_view.shown(pc, PALM) == PALM)

state["fov"], state["arms_fov"] = 110.0, 77.0
moved = arms_view.shown(pc, PALM)
check("with a wider world the spot keeps its distance ahead and moves away from the camera's axis",
      near(moved, (40.0, -25.0 * SPREAD, 50.0 - 20.0 * SPREAD)))
check("the world then shows it where the arms show the hand", near(on_screen(moved, EYE, 110.0), on_screen(PALM, EYE, 77.0)))
check("a spot on the camera's axis does not move", near(arms_view.shown(pc, (60.0, 0.0, 50.0)), (60.0, 0.0, 50.0)))

state["fov"] = 60.0
check("a narrower world, as when aiming down sights, brings the spot towards the axis",
      abs(arms_view.shown(pc, PALM)[1]) < 25.0)
state["fov"] = 110.0

camera.GetCameraRotation = lambda: types.SimpleNamespace(Pitch=0.0, Yaw=90.0)
check("the axis is the camera's: turned a quarter, ahead is along Y",
      near(arms_view.shown(pc, (25.0, 40.0, 30.0)), (25.0 * SPREAD, 40.0, 50.0 - 20.0 * SPREAD)))
camera.GetCameraRotation = lambda: types.SimpleNamespace(Pitch=90.0, Yaw=0.0)
check("looking straight up, ahead is along Z", near(arms_view.shown(pc, (10.0, 5.0, 90.0)), (10.0 * SPREAD, 5.0 * SPREAD, 90.0)))
camera.GetCameraRotation = lambda: types.SimpleNamespace(Pitch=0.0, Yaw=0.0)

for label, world, arms in (("a world view of zero", 0.0, 77.0), ("an arms view of zero", 110.0, 0.0),
                           ("a flat world view", 180.0, 77.0), ("a flat arms view", 110.0, 180.0),
                           ("a view that is not a number", float("nan"), 77.0)):
    report.reset()
    state["fov"], state["arms_fov"] = world, arms
    errors = len(state["errors"])
    kept = arms_view.shown(pc, PALM)
    arms_view.shown(pc, PALM)
    check(f"{label}: the spot is left where it is, said once", kept == PALM and len(state["errors"]) == errors + 1)
state["fov"], state["arms_fov"] = 110.0, 77.0

report.reset()
camera.GetFOVAngle = lambda: 1 / 0
errors = len(state["errors"])
check("a view that cannot be read: the spot is left where it is, said once",
      arms_view.shown(pc, PALM) == PALM and arms_view.shown(pc, PALM) == PALM and len(state["errors"]) == errors + 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
