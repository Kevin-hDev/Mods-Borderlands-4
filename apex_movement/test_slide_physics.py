"""Tests Apex-style slides: slide data prepared once, speed from friction and slope, stop, air, end, restore."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import axle_slide, game, ownership, settings, slide_physics  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(a - b) < tolerance


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


MS = 1_000_000
P = slide_physics
at = sdk_stubs.vector
player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
asset = sdk_stubs.slide_asset(state)
data = movement.ControlledMoveReplicationData
keys = asset.SpeedScaleCurve.EditorCurveData.keys
PER_UNIT = 1130.0 / 1.1017


def curve_values() -> list[float]:
    return [key.Value for key in keys]


def frames(start_ms: int, end_ms: int, step_ms: int = 50) -> None:
    for now_ms in range(start_ms, end_ms + 1, step_ms):
        P.update(player, now_ms * MS)


slowdown = P.friction(1130.0, 1300.0)
check("friction takes the slide speed to the stop speed over the flat distance",
      near(slowdown, (1130.0 ** 2 - 350.0 ** 2) / 2600.0) and near(slowdown, 444.0, 0.01))
check("a floor falling away ahead reads downhill", near(P.downhill(at(0.2, 0.0, 0.98), at(1000.0, 0.0)), 0.2))
check("the same floor climbed reads uphill", near(P.downhill(at(0.2, 0.0, 0.98), at(-500.0, 0.0)), -0.2))
check("a floor sloping sideways reads flat", near(P.downhill(at(0.0, 0.2, 0.98), at(1000.0, 0.0)), 0.0))
check("no speed, no slope", P.downhill(at(0.2, 0.0, 0.98), at(0.0, 0.0)) == 0.0)
check("flat ground slows by the friction", near(P.next_speed(1130.0, 0.5, 0.0, 444.0, 2200.0, 2000.0), 908.0))
check("a slope of about 12 degrees keeps the speed", near(P.next_speed(1130.0, 0.5, 444.0 / 2200.0, 444.0, 2200.0, 2000.0), 1130.0))
check("a steeper slope speeds up, up to the top speed", P.next_speed(1990.0, 1.0, 0.5, 444.0, 2200.0, 2000.0) == 2000.0)
check("uphill slows faster", near(P.next_speed(1130.0, 0.5, -0.2, 444.0, 2200.0, 2000.0), 688.0))
check("speed never goes below zero", P.next_speed(100.0, 1.0, -1.0, 444.0, 2200.0, 2000.0) == 0.0)
check("a scale makes the same slope slow down or speed up that many times harder",
      near(P.next_speed(1130.0, 0.5, 0.0, 444.0, 2200.0, 2000.0, 2.0), 686.0)
      and near(P.next_speed(1130.0, 0.5, 0.5, 444.0, 2200.0, 5000.0, 2.0), 1130.0 + 2.0 * (1100.0 - 444.0) * 0.5))
check("no boost, no gain", near(P.speed_gain(1130.0, axle_slide.NONE), 1.0))
check("starting 25 % faster goes further by the ratio of squares above the stop speed",
      near(P.speed_gain(1130.0, axle_slide.Boost(1.25, 1.0, 1.0)), (1412.5 ** 2 - 350.0 ** 2) / (1130.0 ** 2 - 350.0 ** 2)))

P.update(player, 0)
check("the slide timer is made long", asset.Duration.constant == settings.LONGEST_SLIDE_S)
slope_keys = asset.SpeedSlopeScaleCurve.EditorCurveData.keys
check("the game's slope effect stays switched on, since off it ended every slide", asset.bUseSlopeCurve is True)
check("but its curve is flat at 1, without tangents", [key.Value for key in slope_keys] == [1.0] * 4
      and all(key.ArriveTangent == 0.0 and key.LeaveTangent == 0.0 for key in slope_keys))
check("the speed curve is flat at its start value, without tangents", curve_values() == [1.1017] * 4
      and all(key.ArriveTangent == 0.0 and key.LeaveTangent == 0.0 for key in keys))
check("the game's values are kept to put back", ownership.original(P.DURATION_KEY) == 1.35
      and ownership.original(P.SLOPE_CURVE_KEY).values == (0.5, 1.0, 2.0, 2.0)
      and ownership.original(P.CURVE_KEY).values == (1.1017, 0.9728, 0.7737, 0.3722))
check("the preparation is logged once", notes("slide physics on: duration 30 s") == 1)
P.update(player, 1 * MS)
check("an idle frame prepares nothing again", notes("slide physics on") == 1)

data.ControlledMove = asset
movement.Velocity = at(1130.0, 0.0)
P.update(player, 1000 * MS)
check("a slide starts at the slide speed", near(keys[0].Value * PER_UNIT, 1130.0))
frames(1050, 2000)
check("on flat ground it slows by the friction", near(keys[2].Value * PER_UNIT, 1130.0 - slowdown, 0.01))
check("the whole curve stays flat", len(set(curve_values())) == 1)

movement.CurrentFloor.HitResult.ImpactNormal = at(0.25, 0.0, 0.968)
speed = keys[0].Value * PER_UNIT
frames(2050, 3000)
check("a steep slope ahead cancels the friction and speeds the slide up",
      near(keys[0].Value * PER_UNIT, speed + 2200.0 * 0.25 - slowdown, 0.01))
settings.slide_max_speed.value = 700
P.update(player, 3050 * MS)
check("the top speed caps it", near(keys[0].Value * PER_UNIT, 700.0))
settings.slide_max_speed.value = 2000
movement.CurrentFloor.HitResult.ImpactNormal = at(0.0, 0.0, 1.0)

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
frames(3100, 3500)
check("in the air, off a ramp, the speed is kept", near(keys[0].Value * PER_UNIT, 700.0))
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
P.update(player, 4600 * MS)
check("a long frame counts as a tenth of a second", near(keys[0].Value * PER_UNIT, 700.0 - slowdown * 0.1, 0.01))

frames(4650, 5500)
check("below the stop speed the mod ends the slide", player.calls.count(("SetWantsToSlide", False)) == 1
      and keys[0].Value * PER_UNIT <= P.STOP_SPEED)
frames(5550, 5600)
check("and asks only once", player.calls.count(("SetWantsToSlide", False)) == 1)

data.ControlledMove = None
movement.Velocity = at(300.0, 0.0)
P.update(player, 5650 * MS)
check("the slide's end puts the curve back at its start value", curve_values() == [1.1017] * 4)
check("the end is logged with the model and the game's speed", notes("slide physics end ms=4650 by=mod") == 1
      and notes("game_speed=300") == 1)
check("the end line says how the game's speed compared with the model", notes("game_to_model=") >= 1)

data.ControlledMove = asset
P.update(player, 6000 * MS)
data.ControlledMove = None
P.update(player, 6050 * MS)
check("a slide ended by the game says so", notes("by=game") == 1)
check("a normal slide's end says it had no Axle boost", notes("axle=1.00/1.00/1.00") == 2)


def slide_distance(slope: float, start_ms: int) -> float:
    """One straight slide on ground of this slope until the mod ends it: the distance its model speeds cover."""
    per_unit = axle_slide.start_speed() / 1.1017
    movement.CurrentFloor.HitResult.ImpactNormal = at(slope, 0.0, (1.0 - slope ** 2) ** 0.5)
    movement.Velocity = at(1000.0, 0.0)
    ends = player.calls.count(("SetWantsToSlide", False))
    data.ControlledMove = asset
    now_ms, covered = start_ms, 0.0
    P.update(player, now_ms * MS)
    while player.calls.count(("SetWantsToSlide", False)) == ends and now_ms < start_ms + 60_000:
        covered += keys[0].Value * per_unit * 0.01
        now_ms += 10
        P.update(player, now_ms * MS)
    data.ControlledMove = None
    P.update(player, (now_ms + 10) * MS)
    movement.CurrentFloor.HitResult.ImpactNormal = at(0.0, 0.0, 1.0)
    return covered


flat, uphill, downhill = slide_distance(0.0, 10_000), slide_distance(-0.2, 80_000), slide_distance(0.14, 150_000)
check("a normal flat slide goes the flat distance", abs(flat - 1300.0) < 15.0)
settings.axle_slide.value = True
AXLE_PER_UNIT = 1412.5 / 1.1017
axle_flat, axle_up, axle_down = slide_distance(0.0, 230_000), slide_distance(-0.2, 300_000), slide_distance(0.14, 370_000)
check("an Axle slide goes 50 % further on flat ground", abs(axle_flat / flat - 1.5) < 0.02)
check("25 % further uphill", abs(axle_up / uphill - 1.25) < 0.02)
check("25 % further downhill", abs(axle_down / downhill - 1.25) < 0.02)
check("its end says which boost it had", notes("axle=1.25/1.50/1.25") >= 3)

movement.CurrentFloor.HitResult.ImpactNormal = at(0.5, 0.0, 0.866)
data.ControlledMove = asset
frames(440_000, 450_000)
check("a steep slope takes an Axle slide up to a top speed 25 % higher", near(keys[0].Value * AXLE_PER_UNIT, 2500.0, 0.01))
settings.axle_slide.value = False
frames(450_050, 450_100)
check("switched off mid-slide, the slide keeps the boost it started with",
      near(keys[0].Value * AXLE_PER_UNIT, 2500.0, 0.01))
data.ControlledMove = None
P.update(player, 450_150 * MS)
movement.CurrentFloor.HitResult.ImpactNormal = at(0.0, 0.0, 1.0)
check("and says so at its end", notes("axle=1.25/1.50/1.25") >= 4)
check("the next slide is a normal one", near(axle_slide.start_speed(), 1130.0))

P.reset()
P.update(player, 7000 * MS)
check("after a level change the slide data is prepared again", notes("slide physics on") == 2
      and ownership.original(P.DURATION_KEY) == 1.35 and ownership.original(P.CURVE_KEY).values[1] == 0.9728)

P.stop(player)
check("stop puts the game's timer, slope curve and speed curve back", asset.Duration.constant == 1.35
      and [key.Value for key in slope_keys] == [0.5, 1.0, 2.0, 2.0] and slope_keys[1].LeaveTangent == 1.4
      and curve_values() == [1.1017, 0.9728, 0.7737, 0.3722]
      and [key.LeaveTangent for key in keys] == [-0.2, -0.3, -1.4, 0.0])
check("the restore is logged", notes("slide physics off") == 1)
P.stop(player)
check("a stop with nothing written logs nothing", notes("slide physics off") == 1)

del state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)]
game.forget()
P.update(player, 8000 * MS)
check("a slide asset not loaded yet is reported once and skipped", len(state["errors"]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
