"""Tests the frame: the clock, taking and leaving a vehicle, following the settings, the grip, parts that fail."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Unreadable:
    """An attribute whose value the game will not give."""

    BaseValue = 1000.0

    @property
    def Value(self) -> float:
        raise RuntimeError("unreadable")


def jump(vehicle: sdk_stubs.Vehicle) -> float:
    return vehicle.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant


def seated(vehicle: sdk_stubs.Vehicle) -> types.SimpleNamespace:
    return types.SimpleNamespace(Pawn=vehicle)


state = sdk_stubs.install()

from vehicle_driving import frame, grip, ground, settings  # noqa: E402

MS = 1_000_000
ON_FOOT = types.SimpleNamespace(Pawn=types.SimpleNamespace(Name="OakCharacter_1"))
driver = sdk_stubs.Driver()
attributes = driver.VehicleDriverComponent.VehicleAttributesState
car = sdk_stubs.Vehicle("OakVehicle_1", driver, yaw=90.0)

check("the frame is a clock on every animation update, under the mod's own name",
      frame.tick.path == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation" and frame.tick.kind == "POST"
      and frame.tick.identifier == "vehicle_driving:frame")

state["pc"] = ON_FOOT
frame.on_frame(1000 * MS)
check("on foot nothing is written", state["misc"] == [] and jump(car) == 165.0)

state["pc"] = seated(car)
frame.on_frame(2000 * MS)
check("at the wheel the values are set at once", jump(car) == 330.0 and attributes.MaxAccel.BaseValue == 2500.0
      and "[Vehicle Driving] driving OakVehicle_1" in state["misc"])
settings.jump_height.value = 300
frame.on_frame(2001 * MS)
check("a tick within the same frame does nothing", jump(car) == 330.0)
frame.on_frame(2400 * MS)
check("a moved slider waits for the next check", jump(car) == 330.0)
frame.on_frame(2500 * MS)
check("and is followed within half a second", jump(car) == 495.0)
settings.jump_height.value = 200

car.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
frame.on_frame(2550 * MS)
check("turning at speed, the grip sets the velocity", len(car.Mesh.sets) == 1)
settings.grip.value = False
frame.on_frame(2600 * MS)
check("grip off, the vehicle slides as in the game", len(car.Mesh.sets) == 1)
settings.grip.value = True
car.Mesh.SetPhysicsLinearVelocity = None
frame.on_frame(2650 * MS)
frame.on_frame(2700 * MS)
check("a grip that raises stops alone and is reported once",
      len(state["errors"]) == 1 and "grip stopped until the next vehicle" in state["errors"][0])
frame.on_frame(3000 * MS)
check("the values still follow the settings", jump(car) == 330.0)
settings.jump_height.value = 900
frame.on_frame(3500 * MS)
check("a slider typed above its bounds in the menu is brought back to its top, and the game gets the top",
      settings.jump_height.value == 400 and jump(car) == 660.0)
check("with a warning that says so", any("jump_height=900" in line for line in state["warnings"]))
settings.jump_height.value = 200

state["pc"] = ON_FOOT
frame.on_frame(4000 * MS)
check("getting out puts the game's values back", jump(car) == 165.0 and attributes.MaxAccel.BaseValue == 1000.0
      and state["misc"][-1] == "[Vehicle Driving] left the vehicle, game values back")
count = len(state["misc"])
frame.on_frame(4100 * MS)
check("on foot it stays quiet", len(state["misc"]) == count)

second = sdk_stubs.Vehicle("OakVehicle_2", driver, yaw=90.0)
second.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
state["pc"] = seated(second)
frame.on_frame(5000 * MS)
frame.on_frame(5050 * MS)
check("the next vehicle gets its values and a working grip again", jump(second) == 330.0 and len(second.Mesh.sets) == 1)

sdk_stubs.destroy(second)
state["pc"] = ON_FOOT
frame.on_frame(6000 * MS)
check("a vehicle destroyed under its driver: the driver's values still come back, the wreck is never written",
      attributes.MaxAccel.BaseValue == 1000.0 and jump(second) == 330.0)

broken_driver = sdk_stubs.Driver()
broken_driver.VehicleDriverComponent.VehicleAttributesState.MaxAccel = Unreadable()
third = sdk_stubs.Vehicle("OakVehicle_3", broken_driver, yaw=90.0)
third.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
state["pc"] = seated(third)
frame.on_frame(7000 * MS)
frame.on_frame(7050 * MS)
check("values that raise stop alone and are reported once, and the grip goes on",
      any("values stopped until the next vehicle" in line for line in state["errors"]) and len(third.Mesh.sets) == 1)

lines = frame.stop_all()
check("switching off puts back what was written before the failure",
      [spring.Stiffness for spring in third.OakVehicleMovement.HoverSetup.YawSpring_Hovering.Springs] == [3.0, 3.5, 4.0]
      and broken_driver.VehicleDriverComponent.VehicleAttributesState.maxspeed.BaseValue == 50.0 and lines == [])

wreck = sdk_stubs.Vehicle("OakVehicle_4", driver, yaw=90.0)
state["pc"] = seated(wreck)
frame.on_frame(8000 * MS)
sdk_stubs.destroy(wreck)
count = len(state["misc"])
for step in range(1, 6):
    frame.on_frame(8000 * MS + step * 10 * MS)
check("a vehicle destroyed while still the controller's pawn is let go once, not taken again every frame",
      state["misc"][count:] == ["[Vehicle Driving] left the vehicle, game values back"]
      and attributes.MaxAccel.BaseValue == 1000.0)


def refuse(bone: str) -> None:
    raise ValueError("no body")


odd = sdk_stubs.Vehicle("OakVehicle_5", driver, yaw=90.0)
odd.Mesh.GetPhysicsLinearVelocity = refuse
state["pc"] = seated(odd)
frame.on_frame(9000 * MS)
check("another kind of failure on a later vehicle gets its own line",
      any("grip stopped" in line and "ValueError" in line for line in state["errors"]))

sixth = sdk_stubs.Vehicle("OakVehicle_6", driver, yaw=90.0)
sixth.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
state["pc"] = seated(sixth)
frame.on_frame(10_000 * MS)
bounds_checks: list[int] = []
checked_bounds = settings.keep_in_bounds
settings.keep_in_bounds = lambda: bounds_checks.append(1) or checked_bounds()
for step in range(1, 10):
    frame.on_frame(10_000 * MS + step * 10 * MS)
settings.keep_in_bounds = checked_bounds
check("the bounds are checked twice a second with the other settings, not every frame", bounds_checks == [])
settings.turn_loss.value = 500
errors = len(state["errors"])
frame.on_frame(10_100 * MS)
check("a loss typed beyond its bounds between two checks never reaches the grip: its speed stays a real number",
      len(state["errors"]) == errors and len(sixth.Mesh.sets) > 0
      and all(isinstance(speed, float) for speed in (sixth.Mesh.velocity.X, sixth.Mesh.velocity.Y)))
frame.on_frame(10_500 * MS)
check("and it is brought back at the next check", settings.turn_loss.value == 30)
settings.turn_loss.value = 9
sixth.Mesh = sdk_stubs.Mesh(0.0, 2290.0)
frame.on_frame(10_550 * MS)
settings.grip.value = False
frame.on_frame(10_600 * MS)
sixth.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
settings.grip.value = True
frame.on_frame(12_000 * MS)
check("switched back on after the game stood still over a second, the grip turns nothing at its first frame",
      sixth.Mesh.sets == [])
frame.on_frame(12_050 * MS)
check("then grips again", len(sixth.Mesh.sets) == 1)
for off_ms in (100, 490):
    settings.grip.value = False
    start = frame._last_ns // MS
    for step in range(10, off_ms + 1, 10):
        frame.on_frame((start + step) * MS)
    sixth.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
    settings.grip.value = True
    frame.on_frame((start + off_ms + 10) * MS)
    velocity = sixth.Mesh.velocity
    check(f"the grip off for {off_ms} ms turns one frame's worth when switched back on, not the time it was off",
          abs(math.degrees(math.atan2(velocity.Y, velocity.X)) - grip.GRIP_DEG_PER_S * 0.01) < 0.01)

pusher = sdk_stubs.Vehicle("OakVehicle_7", driver, yaw=90.0)
pusher.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
state["pc"] = seated(pusher)
frame.on_frame(20_000 * MS)
pusher.boosting = True
state["ground"].below = ground.TRACE_UP + 150.0
frame.on_frame(20_050 * MS)
check("boosting off the ground the vehicle is pushed, and the grip rests that frame: its write would wipe the push out",
      len(pusher.Mesh.impulses) == 1 and pusher.Mesh.sets == [])
pusher.boosting = False
frame.on_frame(20_100 * MS)
check("the boost let go, the grip turns the vehicle again",
      len(pusher.Mesh.impulses) == 1 and len(pusher.Mesh.sets) == 1)
settings.air_push.value = 0
pusher.boosting = True
frame.on_frame(20_500 * MS)
frame.on_frame(20_550 * MS)
check("the push's slider is read at the check: at 0 percent the game's boost is alone", len(pusher.Mesh.impulses) == 1)
settings.air_push.value = 100
frame.on_frame(21_000 * MS)
pusher.Mesh.AddImpulse = None
frame.on_frame(21_050 * MS)
frame.on_frame(21_100 * MS)
check("a push that raises stops alone and is reported once",
      sum("air push stopped until the next vehicle" in line for line in state["errors"]) == 1)
check("and the grip goes on", len(pusher.Mesh.sets) > 1)
state["ground"].below = 60.0
frame.stop_all()

# The camera views (spec section 3.8).
watcher = sdk_stubs.Vehicle("OakVehicle_8", driver, yaw=90.0)
camera = sdk_stubs.CameraManager()
held = camera.CameraModeState.CameraLocationOffset
state["pc"] = types.SimpleNamespace(Pawn=watcher, PlayerCameraManager=camera)
frame.on_frame(30_000 * MS)
check("in the game's view the camera is left alone", (held.X, held.Y, held.Z) == (0.0, 0.0, 0.0))
settings.vehicle_view.value = "Close"
frame.on_frame(30_050 * MS)
check("a view chosen is written at the next frame, and said once",
      held.X != 0.0 and state["misc"].count("[Vehicle Driving] camera view Close") == 1)
settings.vehicle_view.value = "Custom"
settings.custom_forward.value = 900
camera.draw()
frame.on_frame(30_500 * MS)
check("Custom's sliders are read at the check, brought back within bounds",
      settings.custom_forward.value == 500 and held.X == 500.0)
state["pc"] = ON_FOOT
frame.on_frame(31_000 * MS)
check("getting out takes our value back", (held.X, held.Y, held.Z) == (0.0, 0.0, 0.0))

settings.vehicle_view.value = "Close"
faulty = sdk_stubs.CameraManager()
faulty.CameraModeState = None
state["pc"] = types.SimpleNamespace(Pawn=watcher, PlayerCameraManager=faulty)
frame.on_frame(32_000 * MS)
frame.on_frame(32_050 * MS)
check("a camera that raises stops alone and is reported once",
      sum("camera stopped until the next vehicle" in line for line in state["errors"]) == 1)
check("and the values still hold", jump(watcher) == 330.0)

ninth = sdk_stubs.Vehicle("OakVehicle_9", driver, yaw=90.0)
kept = sdk_stubs.CameraManager()
state["pc"] = types.SimpleNamespace(Pawn=ninth, PlayerCameraManager=kept)
frame.on_frame(33_000 * MS)
written = kept.CameraModeState.CameraLocationOffset.X
frame.stop_all()
check("switching the mod off takes the camera's value back too",
      written != 0.0 and kept.CameraModeState.CameraLocationOffset.X == 0.0)
settings.vehicle_view.value = "Default"
settings.custom_forward.value = 0

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
