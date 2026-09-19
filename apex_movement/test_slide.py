"""Tests fast slides: start speed through Move_Slide, slide jump speed for 700 ms, slide end logged, restore on stop."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game, ownership, settings, slide, slide_direction, slide_physics, slide_steering  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
asset = sdk_stubs.slide_asset(state)
player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement


def constant() -> float:
    return asset.speed.constant


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


player.ZoomState.bWantsToZoom = True
slide.update(player, 0)
check("aiming leaves the slide speed alone", constant() == 720.0 and not ownership.is_owned(slide.SPEED_KEY))
player.ZoomState.bWantsToZoom = False
player.bIsCrouched = True
slide.update(player, 0)
check("crouched leaves the slide speed alone", constant() == 720.0)
player.bIsCrouched = False
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
slide.update(player, 0)
check("in the air leaves the slide speed alone", constant() == 720.0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

slide.update(player, 1 * MS)
check("standing on the ground sets the constant for a 1130 start", abs(constant() * 1.15 * 1.1017 - 1130.0) < 0.01)
check("the game's constant is kept to put back", ownership.original(slide.SPEED_KEY) == 720.0)
check("the new start speed is logged", notes("slide start speed 1130") == 1)
slide.update(player, 2 * MS)
check("an unchanged speed is not written or logged again", notes("slide start speed") == 1)

settings.slide_speed.value = 1200
slide.update(player, 3 * MS)
check("the slide slider applies at the next frame standing on the ground",
      abs(constant() * 1.15 * 1.1017 - 1200.0) < 0.01)
settings.slide_speed.value = 1130

settings.axle_slide.value = True
slide.update(player, 3500 * 1000)
check("an Axle slide starts 25 % faster", abs(constant() * 1.15 * 1.1017 - 1412.5) < 0.01)
settings.axle_slide.value = False
slide.update(player, 3600 * 1000)
check("switched off, slides start at the slide speed again", abs(constant() * 1.15 * 1.1017 - 1130.0) < 0.01)

# The speed bonus stays at 1.15: at 1.0 dividing by it or not gives the same constant, and the check proves nothing.
asset.bSpeedAffectedByMaxGroundSpeedScale = False
slide.update(player, 4 * MS)
check("an asset not scaled by the speed bonus divides by the curve only", abs(constant() * 1.1017 - 1130.0) < 0.01)
asset.bSpeedAffectedByMaxGroundSpeedScale = True
slide.update(player, 5 * MS)

settings.sprint_speed.value = 1500
slide.update(player, 6 * MS)
check("a slide slower than the sprint starts at the sprint speed", abs(constant() * 1.15 * 1.1017 - 1500.0) < 0.01)
settings.sprint_speed.value = 960
slide.update(player, 7 * MS)

movement.ControlledMoveReplicationData.ControlledMove = asset
movement.Velocity = sdk_stubs.vector(600.0, 600.0, 50.0)
slide.update(player, 100 * MS)
speed = math.hypot(movement.Velocity.X, movement.Velocity.Y)
check("early in a slide the velocity is raised to the slide speed", abs(speed - 1130.0) < 0.01)
check("the raised velocity keeps its direction", abs(movement.Velocity.X - movement.Velocity.Y) < 1e-9)
check("the raised velocity keeps its vertical part", movement.Velocity.Z == 50.0)

settings.axle_slide.value = True
movement.Velocity = sdk_stubs.vector(900.0, 0.0)
slide.update(player, 120 * MS)
check("the Axle slide switched on mid-slide leaves that slide at the speed it started with, as slide physics does",
      movement.Velocity.X == 1130.0)
settings.axle_slide.value = False

written, logged = constant(), notes("slide start speed")
asset.SpeedScaleCurve.EditorCurveData.keys[0].Value = 0.8
slide.update(player, 150 * MS)
check("during a slide, standing, the constant does not follow the curve slide physics lowers",
      constant() == written and notes("slide start speed") == logged)
asset.SpeedScaleCurve.EditorCurveData.keys[0].Value = 1.1017

movement.Velocity = sdk_stubs.vector(1200.0, 0.0)
slide.update(player, 200 * MS)
check("a slide already faster, downhill, is left alone", movement.Velocity.X == 1200.0)

movement.Velocity = sdk_stubs.vector(900.0, 0.0)
slide.update(player, 800 * MS)
check("the velocity is still raised at 700 ms", movement.Velocity.X == 1130.0)
movement.Velocity = sdk_stubs.vector(900.0, 0.0)
slide.update(player, 801 * MS)
check("past 700 ms the slide keeps the game's speed", movement.Velocity.X == 900.0)

movement.ControlledMoveReplicationData.ControlledMove = None
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.Velocity = sdk_stubs.vector(1134.0, 0.0)
slide.update(player, 820 * MS)
check("a slide ending in the air is logged with its length and speeds",
      notes("slide end on=air ms=720 top_speed=1200 speed_now=1134") == 1)
slide.update(player, 830 * MS)
check("a slide end is logged once", notes("slide end") == 1)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

movement.ControlledMoveReplicationData.ControlledMove = types.SimpleNamespace(name="Move_Dash")
movement.Velocity = sdk_stubs.vector(500.0, 0.0)
slide.update(player, 900 * MS)
check("another controlled move, such as a dash, is not boosted", movement.Velocity.X == 500.0)
movement.ControlledMoveReplicationData.ControlledMove = None

movement.ControlledMoveReplicationData.ControlledMove = asset
slide.update(player, 1000 * MS)
slide.reset()
movement.ControlledMoveReplicationData.ControlledMove = None
slide.update(player, 1010 * MS)
check("after a reset no stale slide end is logged", notes("slide end") == 1)

key = ("OakControlledMove", sdk_stubs.SLIDE_PATH)
del state["objects"][key]
game.forget()
slide.update(player, 1100 * MS)
slide.update(player, 1101 * MS)
check("a slide asset not loaded yet skips the frame and is reported once", len(state["errors"]) == 1)
for module in (slide_physics, slide_direction, slide_steering):
    module.update(player, 1102 * MS)
check("one line reports it for every module of the slides", len(state["errors"]) == 1)
check("in words true of all of them, not of the slide speed only",
      "Move_Slide not found yet" in state["errors"][0] and "speed" not in state["errors"][0])
state["objects"][key] = asset

# Slides switched off and on again during one slide: the frame loop calls stop, then update on the same slide.
movement.ControlledMoveReplicationData.ControlledMove = asset
movement.Velocity = sdk_stubs.vector(900.0, 0.0)
slide.update(player, 1200 * MS)
slide.stop(player)
movement.Velocity = sdk_stubs.vector(900.0, 0.0)
slide.update(player, 1250 * MS)
check("switched off and on during one slide, that slide keeps the game's speed", movement.Velocity.X == 900.0)
movement.ControlledMoveReplicationData.ControlledMove = None
slide.update(player, 1300 * MS)
movement.ControlledMoveReplicationData.ControlledMove = asset
slide.update(player, 1350 * MS)
check("the next slide is raised again", movement.Velocity.X == 1130.0)
movement.ControlledMoveReplicationData.ControlledMove = None
slide.update(player, 1400 * MS)

slide.stop(player)
check("stop puts the game's slide speed back", constant() == 720.0 and not ownership.is_owned(slide.SPEED_KEY))
slide.stop(None)
check("stop with nothing written does not raise", constant() == 720.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
