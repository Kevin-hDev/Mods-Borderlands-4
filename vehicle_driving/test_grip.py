"""Tests the grip: the velocity turned toward the facing, the loss per degree, what it leaves alone, the hold limit."""

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


def heading(x: float, y: float) -> float:
    return math.degrees(math.atan2(y, x))


def moving(yaw: float, x: float, y: float = 0.0, z: float = 0.0, slide: str = "None") -> sdk_stubs.Vehicle:
    vehicle = sdk_stubs.Vehicle(yaw=yaw, slide=slide)
    vehicle.Mesh = sdk_stubs.Mesh(x, y, z)
    return vehicle


state = sdk_stubs.install()

from vehicle_driving import grip  # noqa: E402

MS = 1_000_000
LOSS = 0.001

x, y = grip.gripped(2290.0, 0.0, 90.0, 30.0, LOSS)
check("the velocity turns toward the facing by the allowed angle", near(heading(x, y), 30.0))
check("each degree turned costs the set share", near(math.hypot(x, y), 2290.0 * (1 - LOSS) ** 30))
check("at no loss the speed is kept", near(math.hypot(*grip.gripped(2290.0, 0.0, 90.0, 30.0, 0.0)), 2290.0))
x, y = grip.gripped(2290.0, 0.0, 10.0, 30.0, LOSS)
check("a small gap is closed at once", near(heading(x, y), 10.0))
check("a gap under the threshold is left alone",
      grip.gripped(2290.0, 0.0, grip.MIN_GAP_DEG / 2, 30.0, LOSS) == (2290.0, 0.0))
x, y = grip.gripped(2290.0 * math.cos(math.radians(170.0)), 2290.0 * math.sin(math.radians(170.0)), -170.0, 30.0, LOSS)
check("the short way round, across half a turn: from 170 to -170", near(heading(x, y), -170.0))
check("a slow vehicle is left alone", grip.gripped(200.0, 0.0, 90.0, 30.0, LOSS) == (200.0, 0.0))
check("a vehicle going backward is left alone", grip.gripped(-1000.0, 0.0, 0.0, 30.0, LOSS) == (-1000.0, 0.0))

car = moving(90.0, 2290.0, z=-50.0)
session = grip.Grip(0)
session.step(50 * MS, car, LOSS)
written, add, bone = car.Mesh.sets[-1]
check("a frame turns the velocity by the rate times the frame's time",
      near(heading(written.X, written.Y), grip.GRIP_DEG_PER_S * 0.05))
check("the speed loses its share of the turn",
      near(math.hypot(written.X, written.Y), 2290.0 * (1 - LOSS) ** (grip.GRIP_DEG_PER_S * 0.05)))
check("the height speed is kept", written.Z == -50.0)
check("the velocity is set on the whole body, not added: an impulse's velocity change is ignored (session 6)",
      add is False and bone == "None")

straight = moving(1.0, 2290.0)
session.step(100 * MS, straight, LOSS)
check("a vehicle going nearly straight is left alone: set every frame in a straight line, the speed froze (session 4)",
      straight.Mesh.sets == [])
powerslide = moving(90.0, 2290.0, slide="JumpAndSlide")
session.step(150 * MS, powerslide, LOSS)
check("the game's powerslide is left alone", powerslide.Mesh.sets == [])
state["ground"].below = None
airborne = moving(90.0, 2290.0)
session.step(200 * MS, airborne, LOSS)
check("with no ground under it the vehicle is left alone: written in the air, a jump climbed to 361 m (session 7)",
      airborne.Mesh.sets == [])
state["ground"].below = 60.0
climbing = moving(90.0, 2290.0, z=grip.MAX_VERTICAL + 1.0)
session.step(250 * MS, climbing, LOSS)
check("a vehicle rising or falling fast is left alone", climbing.Mesh.sets == [])
hitch = moving(90.0, 2290.0)
session.step(10_000 * MS, hitch, LOSS)
velocity = hitch.Mesh.velocity
check("a long hitch turns no more than one tenth of a second's worth",
      near(heading(velocity.X, velocity.Y), grip.GRIP_DEG_PER_S * grip.MAX_STEP_S))

holding = grip.Grip(0)
turning = moving(90.0, 2290.0)
turning.K2_GetActorRotation = lambda: sdk_stubs.rotator(
    heading(turning.Mesh.velocity.X, turning.Mesh.velocity.Y) + 30.0)
written_at = []
for step in range(1, 400):
    before = len(turning.Mesh.sets)
    holding.step(step * 10 * MS, turning, 0.0)
    if len(turning.Mesh.sets) > before:
        written_at.append(step * 10 * MS)
gaps = [later - earlier for earlier, later in zip(written_at, written_at[1:])]
check("a turn that never ends is still let go now and then, so the game's own velocity comes back",
      max(gaps) >= grip.REST_NS and written_at[-1] - written_at[0] > grip.MAX_HOLD_NS)
check("the rest comes after the hold, not before",
      written_at[0] + grip.MAX_HOLD_NS <= written_at[gaps.index(max(gaps))])

reporting = grip.Grip(0)
summary = moving(90.0, 2290.0)
lines: list[str] = []
for step in range(60):
    lines += reporting.step(10 * MS + step * 100 * MS, summary, LOSS)
check("a summary line every five seconds shows the grip at work",
      [line for line in lines if line.startswith("grip frames=")] == ["grip frames=4 largest_turn=36.0"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
