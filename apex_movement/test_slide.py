"""Tests fast slides: start speed through Move_Slide, slide jump speed for 700 ms, slide end logged, restore on stop."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import (game, guest_trust, guests, ownership, settings, slide, slide_direction,  # noqa: E402
                           slide_physics, slide_steering)

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
check("aiming leaves the slide speed alone", constant() == 720.0 and not ownership.is_owned(slide.SPEED_KEY)
      and asset.bSpeedAffectedByMaxGroundSpeedScale is True)
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
check("standing on the ground sets the constant for a 1130 start", abs(constant() * 1.1017 - 1130.0) < 0.01)
check("the game's constant is kept to put back", ownership.original(slide.SPEED_KEY) == 720.0)
check("the game keeps multiplying the slide by each character's scale, which carries the slide's speed",
      asset.bSpeedAffectedByMaxGroundSpeedScale is True)
movement.MaxGroundSpeedScale.Value = 1.42
slide.update(player, 1 * MS + 1)
check("a character with another speed bonus gets the same constant", abs(constant() * 1.1017 - 1130.0) < 0.01)
movement.MaxGroundSpeedScale.Value = 1.15
check("the new start speed is logged", notes("slide start speed 1130") == 1)
slide.update(player, 2 * MS)
check("an unchanged speed is not written or logged again", notes("slide start speed") == 1)

settings.slide_speed.value = 1200
slide.update(player, 3 * MS)
check("the slide slider applies at the next frame standing on the ground",
      abs(constant() * 1.1017 - 1200.0) < 0.01)
settings.slide_speed.value = 1130

settings.axle_slide.value = True
slide.update(player, 3500 * 1000)
check("an Axle slide starts 25 % faster", abs(constant() * 1.1017 - 1412.5) < 0.01)
settings.axle_slide.value = False
slide.update(player, 3600 * 1000)
check("switched off, slides start at the slide speed again", abs(constant() * 1.1017 - 1130.0) < 0.01)


settings.sprint_speed.value = 1500
slide.update(player, 6 * MS)
check("a slide slower than the sprint starts at the sprint speed", abs(constant() * 1.1017 - 1500.0) < 0.01)
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

# A co-op host gives each guest the slide jump's speed, as the guest's own game does.
guest = sdk_stubs.FakeCharacter("OakCharacter_guest", local=False)
guest_movement = guest.CharacterMovement
memo: dict = {}


def guest_frame(now_ns: int) -> dict:
    return slide.for_guest(guests.GuestFrame(guest, now_ns, lambda field: None, memo))


guest_movement.ControlledMoveReplicationData.ControlledMove = asset
guest_movement.Velocity = sdk_stubs.vector(900.0, 0.0)
check("during a guest's slide the host takes the guest's place", guest_frame(2000 * MS) == guest_trust.SWITCHES)
check("a slide begun before the host followed the guest keeps the game's speed", guest_movement.Velocity.X == 900.0)
guest_movement.ControlledMoveReplicationData.ControlledMove = None
check("a slide over on the ground gives the guest back to the host's corrections", guest_frame(2010 * MS) == {})
check("off a slide the guest's speed is left alone", guest_movement.Velocity.X == 900.0)
guest_movement.ControlledMoveReplicationData.ControlledMove = asset
guest_movement.Velocity = sdk_stubs.vector(600.0, 600.0, 50.0)
guest_frame(2020 * MS)
guest_speed = math.hypot(guest_movement.Velocity.X, guest_movement.Velocity.Y)
check("early in a guest's slide its speed is raised to the slide speed", abs(guest_speed - 1130.0) < 0.01)
check("the guest keeps its direction and vertical speed",
      abs(guest_movement.Velocity.X - guest_movement.Velocity.Y) < 1e-9 and guest_movement.Velocity.Z == 50.0)
check("the player's own speed is not touched by the guest's slide", movement.Velocity.X != guest_movement.Velocity.X)
guest_movement.Velocity = sdk_stubs.vector(1200.0, 0.0)
guest_frame(2100 * MS)
check("a guest's slide already faster is left alone", guest_movement.Velocity.X == 1200.0)
guest_movement.Velocity = sdk_stubs.vector(900.0, 0.0)
guest_frame(2720 * MS)
check("a guest's slide is still raised at 700 ms from when the host saw it", guest_movement.Velocity.X == 1130.0)
guest_movement.Velocity = sdk_stubs.vector(900.0, 0.0)
guest_frame(2721 * MS)
check("past 700 ms the guest's slide keeps the game's speed", guest_movement.Velocity.X == 900.0)
settings.axle_slide.value = True
guest_movement.ControlledMoveReplicationData.ControlledMove = None
guest_frame(2800 * MS)
guest_movement.ControlledMoveReplicationData.ControlledMove = asset
guest_frame(2810 * MS)
check("the next guest slide is raised again, to the host's Axle speed", abs(guest_movement.Velocity.X - 1412.5) < 0.01)
settings.axle_slide.value = False
guest_movement.ControlledMoveReplicationData.ControlledMove = None
guest_movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("a slide left by a jump keeps the host on the guest's place in the air",
      guest_frame(2850 * MS) == guest_trust.SWITCHES)
guest_movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
check("until the guest lands", guest_frame(2860 * MS) == {})
guest_movement.ControlledMoveReplicationData.ControlledMove = types.SimpleNamespace(name="Move_Dash")
guest_movement.Velocity = sdk_stubs.vector(500.0, 0.0)
guest_frame(2900 * MS)
check("a guest's dash is not boosted", guest_movement.Velocity.X == 500.0)
guest_movement.ControlledMoveReplicationData.ControlledMove = None

slide.stop(player)
check("stop puts the game's slide speed back", constant() == 720.0 and not ownership.is_owned(slide.SPEED_KEY))
slide.stop(None)
check("stop with nothing written does not raise", constant() == 720.0)

counted = sdk_stubs.FakeCharacter()
asked: list[int] = []
ask_game = counted.CharacterMovement.IsPerformingControlledMove
counted.CharacterMovement.IsPerformingControlledMove = lambda: asked.append(1) or ask_game()
slide.update(counted, 3000 * MS)
check("standing on the ground, the game is asked once a frame whether a slide is under way", len(asked) == 1)
slide.stop(counted)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
