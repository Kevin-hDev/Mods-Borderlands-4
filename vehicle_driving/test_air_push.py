"""Tests the push in the air: flat toward the nose, up to the boost's top speed, only boosting off the ground."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a: float, b: float) -> bool:
    return abs(a - b) < 0.01


def flying(yaw: float = 0.0, x: float = 1000.0, boosting: bool = True) -> sdk_stubs.Vehicle:
    """A vehicle falling at 500, so that a push copying the vertical speed shows."""
    vehicle = sdk_stubs.Vehicle(yaw=yaw)
    vehicle.Mesh = sdk_stubs.Mesh(x, 0.0, -500.0)
    vehicle.boosting = boosting
    return vehicle


state = sdk_stubs.install()

from vehicle_driving import air_push, ground  # noqa: E402

MS = 1_000_000
MASS = 2500.0
# The stub driver's BoostMaxAccel and BoostMaxSpeed values, untouched by any setting here.
ACCEL = 1615.08
CEILING = 66.3425 * air_push.CM_S_PER_MPH

check("the push goes toward the nose, flat", air_push.push(1000.0, 0.0, 0.0, 200.0, 3000.0) == (200.0, 0.0))
x, y = air_push.push(1000.0, 0.0, 90.0, 200.0, 3000.0)
check("toward the nose even when the vehicle moves another way", near(x, 0.0) and near(y, 200.0))
x, y = air_push.push(2900.0, 0.0, 0.0, 200.0, 3000.0)
check("never past the ceiling", near(x, 100.0) and near(y, 0.0))
x, y = air_push.push(2900.0, 0.0, 90.0, 5000.0, 3000.0)
check("sideways too, the speed it gives stops at the ceiling", near(math.hypot(2900.0 + x, y), 3000.0))
check("at the ceiling or past it, nothing: the push never brakes",
      air_push.push(3000.0, 0.0, 0.0, 200.0, 3000.0) is None
      and air_push.push(3500.0, 0.0, 180.0, 200.0, 3000.0) is None)
check("no gain, nothing", air_push.push(1000.0, 0.0, 0.0, 0.0, 3000.0) is None)

state["ground"].below = None
pusher = air_push.AirPush(0)
car = flying()
pushed, _lines = pusher.step(50 * MS, car, 1.0)
impulse, bone, velocity_change = car.Mesh.impulses[-1]
check("boosting in the air, a frame pushes", pushed and len(car.Mesh.impulses) == 1)
check("an impulse of the mass times the boost's ground push for the frame's time, toward the nose",
      near(impulse.X, MASS * ACCEL * 0.05) and near(impulse.Y, 0.0))
check("flat: the game's vertical speed and gravity are left alone (session 7)", impulse.Z == 0.0)
check("a plain impulse on the whole body: the velocity-change flag is ignored by the game (session 6)",
      bone == "None" and velocity_change is False)
check("the push never sets the velocity", car.Mesh.sets == [])
_context, start, end, *_rest = state["ground"].calls[-1]
check("the trace looks for ground within the push's own reach",
      near(start.Z - end.Z, ground.TRACE_UP + air_push.AIR_REACH))
pusher.step(100 * MS, car, 3.0)
check("at 300 percent, three times the push", near(car.Mesh.impulses[-1][0].X, 3 * MASS * ACCEL * 0.05))
state["ground"].below = ground.TRACE_UP + 150.0
check("ground 1.5 under the origin is in the air for the push: a jump counts almost from its start",
      pusher.step(150 * MS, car, 1.0)[0])
state["ground"].below = 60.0
check("on the ground, nothing", not pusher.step(200 * MS, car, 1.0)[0])
state["ground"].below = None
idle = flying(boosting=False)
check("without the game's boost, nothing: the push follows the game's boost and its gauge",
      not pusher.step(250 * MS, idle, 1.0)[0] and idle.Mesh.impulses == [])
check("at 0 percent, nothing", not pusher.step(300 * MS, car, 0.0)[0])
fast = flying(x=CEILING + 1.0)
check("at the boost's top speed, nothing: its ceiling is the boost's own, as on the ground",
      not pusher.step(350 * MS, fast, 1.0)[0])
driverless = flying()
driverless.DriverPawn = None
check("no driver yet, nothing and no error", not pusher.step(400 * MS, driverless, 1.0)[0])
calls = len(state["ground"].calls)
pusher.step(450 * MS, idle, 1.0)
pusher.step(500 * MS, fast, 1.0)
check("the trace comes last: a frame with nothing to push costs no trace", len(state["ground"].calls) == calls)
check("after the game stood still, the first frame pushes nothing", not pusher.step(10_000 * MS, car, 1.0)[0])
pusher.step(10_400 * MS, car, 1.0)
check("a hitch pushes no more than one tenth of a second's worth",
      near(car.Mesh.impulses[-1][0].X, MASS * ACCEL * air_push.MAX_STEP_S))

reporting = air_push.AirPush(0)
lines: list[str] = []
for step in range(60):
    lines += reporting.step(10 * MS + step * 100 * MS, flying(), 1.0)[1]
check("a summary line every five seconds shows the push at work",
      [line for line in lines if line.startswith("air push")] == ["air push frames=50 top_speed=1000"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
