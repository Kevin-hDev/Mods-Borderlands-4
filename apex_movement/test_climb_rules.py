"""Tests the wall climb's rules: every start condition and the reason it gives, every end, the wait and what
clears it. The angles and the direction of a climb are climb_aim's, tested next to it."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import climb_rules as rules  # noqa: E402
from apex_movement.climb_aim import Wall  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
WALL = Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=1.0)
LIMITS = rules.Limits(height=372.0, delay_ns=1500 * MS, lean_deg=60.0)


def moment(now_ms: int, **changes: object) -> rules.Moment:
    values: dict = dict(now_ns=now_ms * MS, in_air=True, on_ground=False, game_move=False, mantling=False,
                        near_game_climb=False, z=0.0, jumps=1, stick_x=1.0, stick_y=0.0, view_yaw=0.0, wall=WALL, hits=5, high_wall=True)
    values.update(changes)
    return rules.Moment(**values)


def turned(degrees: float) -> dict:
    return {"stick_x": math.cos(math.radians(degrees)), "stick_y": math.sin(math.radians(degrees))}


def starts(**changes: object) -> bool:
    return rules.Rules().step(moment(0, **changes), LIMITS).event == "start"


check("in the air, a wall in reach, stick and camera toward it: a climb starts", starts())
check("the climb pushes from its first frame", rules.Rules().step(moment(0), LIMITS).climbing)
check("on the ground nothing starts", not starts(in_air=False, on_ground=True))
check("without a wall nothing starts", not starts(wall=None))
check("a wall out of reach starts nothing", not starts(wall=Wall(distance=91.0, into_x=1.0, into_y=0.0, flat=1.0)))
check("a wall right at the reach starts", starts(wall=Wall(distance=90.0, into_x=1.0, into_y=0.0, flat=1.0)))
check("a stick pushed less than halfway starts nothing", not starts(stick_x=0.4))
check("a stick 70 degrees off the wall starts nothing", not starts(**turned(70.0)))
check("a stick 55 degrees off starts: the diagonal of the slider is allowed from the first frame",
      starts(**turned(55.0)))
check("a camera 70 degrees off the wall starts nothing", not starts(view_yaw=70.0))
check("a camera 55 degrees off starts: it follows the diagonal like the stick", starts(view_yaw=55.0))
check("without a camera heading nothing starts", not starts(view_yaw=None))
check("during a dash or a slide nothing starts", not starts(game_move=True))
check("during a mantle nothing starts", not starts(mantling=True))
check("near a game climbing wall nothing starts: the game keeps its climb", not starts(near_game_climb=True))


def after(**changes: object) -> rules.Step:
    one = rules.Rules()
    one.step(moment(0), LIMITS)
    values: dict = {"z": 50.0}
    values.update(changes)
    return one.step(moment(100, **values), LIMITS)


check("nothing changed: the climb goes on", after().climbing and after().event == "")
check("the game's mantle ends it", after(mantling=True, in_air=False).event == rules.MANTLE)
check("landing ends it", after(in_air=False, on_ground=True).event == rules.LANDED)
check("a dash ends it", after(game_move=True).event == rules.GAME_MOVE)
check("another game mode ends it", after(in_air=False).event == rules.GAME_MOVE)
check("a jump ends it", after(jumps=2).event == rules.JUMP)
given_back = rules.Rules()
given_back.step(moment(0, jumps=2), LIMITS)
given_back.jumps_given_back(1)
check("a jump count given back keeps the climb", given_back.step(moment(100, jumps=1), LIMITS).climbing)
check("and a jump above it ends the climb", given_back.step(moment(200, jumps=2), LIMITS).event == rules.JUMP)
check("no wall any more ends it", after(wall=None).event == rules.WALL_LOST)
check("a wall past 135 ends it", after(wall=Wall(distance=136.0, into_x=1.0, into_y=0.0, flat=1.0)).event == rules.WALL_LOST)
check("a wall at 135 keeps it", after(wall=Wall(distance=135.0, into_x=1.0, into_y=0.0, flat=1.0)).climbing)
check("a stick let go for a moment keeps the climb", after(stick_x=0.1).climbing)
let_go = rules.Rules()
let_go.step(moment(0), LIMITS)
let_go.step(moment(100, stick_x=0.1), LIMITS)
check("still let go a quarter of a second later, it ends", let_go.step(moment(360, stick_x=0.1), LIMITS).event == rules.STICK)
flicked = rules.Rules()
flicked.step(moment(0), LIMITS)
flicked.step(moment(100, z=40.0, stick_x=0.1), LIMITS)
flicked.step(moment(200, z=80.0), LIMITS)
check("pushed again in between, the count starts over",
      flicked.step(moment(400, z=160.0, stick_x=0.1), LIMITS).climbing)
check("a stick turned 50 degrees keeps it, as it follows a camera turned 50 degrees", after(**turned(50.0)).climbing)
check("a stick turned 70 degrees keeps it: the 15 degree margin past the diagonal", after(**turned(70.0)).climbing)
turned_away = rules.Rules()
turned_away.step(moment(0), LIMITS)
turned_away.step(moment(100, **turned(80.0)), LIMITS)
check("a stick turned 80 degrees ends it once the grace is over",
      turned_away.step(moment(400, **turned(80.0)), LIMITS).event == rules.STICK)
check("a camera turned 70 degrees keeps it: the same margin past the diagonal", after(view_yaw=70.0).climbing)
check("a camera turned 80 degrees ends it", after(view_yaw=80.0).event == rules.CAMERA)
check("a camera and stick turned together are told as the camera, which forgives nothing",
      after(view_yaw=80.0, **turned(80.0)).event == rules.CAMERA)
ended = rules.Rules()
ended.step(moment(0), LIMITS)
ended.step(moment(100, z=50.0, view_yaw=80.0), LIMITS)
check("an end gives the rise and the time", (ended.start is None
      and rules.Rules().step(moment(0), LIMITS).climbing))
ended_step = rules.Rules()
ended_step.step(moment(0), LIMITS)
step = ended_step.step(moment(100, z=50.0, view_yaw=80.0), LIMITS)
check("with its rise and its time", (step.rise, step.ms) == (50.0, 100))

high = rules.Rules()
high.step(moment(0, z=1000.0), LIMITS)
check("the height is counted from where the climb started", high.step(moment(100, z=1371.0), LIMITS).climbing)
check("reaching it ends the climb", high.step(moment(200, z=1372.0), LIMITS).event == rules.HEIGHT)

stuck = rules.Rules()
stuck.step(moment(0), LIMITS)
check("rising keeps the climb", stuck.step(moment(100, z=36.0), LIMITS).climbing)
check("less than 0.2 s without rising keeps it", stuck.step(moment(250, z=38.0), LIMITS).climbing)
check("0.2 s without rising 10, stuck under something, ends it", stuck.step(moment(300, z=40.0), LIMITS).event == rules.BLOCKED)
check("and blocks the next climb", stuck.step(moment(400, z=40.0), LIMITS).event == "")

settle = rules.Rules()
settle.step(moment(0, jumps=0), LIMITS)
check("the jump count catching up just after the take-off is no new jump", settle.step(moment(20, jumps=1), LIMITS).climbing)
check("a jump after that ends the climb", settle.step(moment(200, jumps=2), LIMITS).event == rules.JUMP)

wait = rules.Rules()
wait.step(moment(0), LIMITS)
wait.step(moment(100, view_yaw=80.0), LIMITS)
check("a climb that ended short blocks the next one", wait.step(moment(200), LIMITS).event == "")
check("until the 1.5 s wait is over", wait.step(moment(1600), LIMITS).event == "start")

for reason, changes in ((rules.GAME_MOVE, {"game_move": True}), (rules.JUMP, {"jumps": 2}),
                        (rules.WALL_LOST, {"wall": None}), (rules.CAMERA, {"view_yaw": 80.0}), (rules.HEIGHT, {"z": 400.0})):
    one = rules.Rules()
    one.step(moment(0), LIMITS)
    one.step(moment(100, **changes), LIMITS)
    check(f"an end by {reason} blocks the next climb too", one.step(moment(200), LIMITS).event == "")

landed = rules.Rules()
landed.step(moment(0), LIMITS)
landed.step(moment(100, view_yaw=80.0), LIMITS)
landed.step(moment(150, in_air=False, on_ground=True), LIMITS)
check("landing clears the wait", landed.step(moment(200), LIMITS).event == "start")

over = rules.Rules()
over.step(moment(0), LIMITS)
over.step(moment(100, mantling=True, in_air=False), LIMITS)
check("a climb the game finished with a mantle blocks nothing", over.step(moment(800), LIMITS).event == "start")

free = rules.Rules()
free.step(moment(0), LIMITS)
free.step(moment(100, view_yaw=80.0), rules.Limits(height=372.0, delay_ns=0, lean_deg=60.0))
check("with no wait set, a new climb may start at once", free.step(moment(101), LIMITS).event == "start")

count = 0
many = rules.Rules()
for n in range(5):
    if many.step(moment(n * 2000), LIMITS).event == "start":
        count += 1
    many.step(moment(n * 2000 + 100, view_yaw=80.0), LIMITS)
check("no limit on the number of climbs, one wait apart", count == 5)


# The one angle that rules the stick: the diagonal of the slider, never under 45 degrees at the start.
STRAIGHT = rules.Limits(height=372.0, delay_ns=0, lean_deg=0.0)
WIDE = rules.Limits(height=372.0, delay_ns=0, lean_deg=75.0)
check("a climb may start on a stick within the diagonal, never under 45 degrees",
      rules.start_angle(STRAIGHT) == 45.0 and rules.start_angle(LIMITS) == 60.0 and rules.start_angle(WIDE) == 75.0)
check("with no diagonal a stick 40 degrees off starts and 50 does not",
      rules.Rules().step(moment(0, **turned(40.0)), STRAIGHT).event == "start"
      and rules.Rules().step(moment(0, **turned(50.0)), STRAIGHT).event == "")
check("the widest diagonal starts on a stick 70 degrees off", rules.Rules().step(moment(0, **turned(70.0)), WIDE).event == "start")


# Why a climb did not start: one name per refusal, the same conditions the start itself uses.
def refused(**changes: object) -> str:
    return rules.Rules().start_refusal(moment(0, **changes), LIMITS)


check("nothing in the way: no refusal", refused() == "")
check("on the ground", refused(in_air=False) == rules.ON_GROUND)
check("during a dash or a slide, and during the game's own mantle, each named apart",
      refused(game_move=True) == rules.GAME_MOVE_BUSY and refused(mantling=True) == rules.MANTLING)
check("near the game's own climbing wall", refused(near_game_climb=True) == rules.GAME_CLIMB)
check("nothing in front", refused(wall=None) == rules.NO_WALL)
check("a wall too far", refused(wall=Wall(distance=91.0, into_x=1.0, into_y=0.0, flat=1.0)) == rules.TOO_FAR)
check("a face leaning too much to be a wall",
      refused(wall=Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.69)) == rules.SLOPE)
check("a face just upright enough is no refusal",
      refused(wall=Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.7)) == "")
check("a stick barely pushed", refused(stick_x=0.4) == rules.NO_STICK)
check("a wall seen only below the waist: a step, not a wall", refused(high_wall=False) == rules.LOW_ONLY)
check("a stick turned away", refused(**turned(70.0)) == rules.STICK)
check("a camera turned away", refused(view_yaw=70.0) == rules.CAMERA)

waited = rules.Rules()
waited.step(moment(0), LIMITS)
waited.step(moment(100, view_yaw=80.0), LIMITS)
check("during the wait that follows a short climb", waited.start_refusal(moment(200), LIMITS) == rules.WAITING)
check("a leaning face also ends a climb under way",
      after(wall=Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.5)).event == rules.WALL_LOST)

# Which surface a climb judges itself on, out of what the traces met.
def pick(*walls: rules.Wall) -> rules.Wall | None:
    return rules.best_wall(list(walls))


PANEL = Wall(distance=98.0, into_x=1.0, into_y=0.0, flat=1.0)
BEVEL = Wall(distance=2.0, into_x=1.0, into_y=0.0, flat=0.53)
NEARER = Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.80)

check("nothing met, nothing picked", pick() is None)
check("a bevel at arm's length does not hide the panel behind it: it is not upright enough to be a wall",
      pick(BEVEL, PANEL) is PANEL)
merged = pick(PANEL, NEARER)
check("two heights seeing the same wall are merged: its nearest distance, its best uprightness",
      merged.distance == 60.0 and merged.flat == 1.0)
SIDE = Wall(distance=70.0, into_x=0.0, into_y=1.0, flat=1.0)
check("a wall facing another way is not merged in: the nearest one alone is taken",
      pick(NEARER, SIDE) is NEARER)
bar = Wall(distance=50.0, into_x=0.94, into_y=0.34, flat=0.9)
smoothed = pick(bar, NEARER)
check("a bar standing proud of the face is smoothed into it, not followed on its own",
      round(smoothed.into_x, 2) == 0.98 and round(smoothed.into_y, 2) == 0.17)
check("with no upright surface at all, the nearest is picked so a refusal can describe it",
      pick(BEVEL, Wall(distance=9.0, into_x=1.0, into_y=0.0, flat=0.2)) is BEVEL)

# Every refusal the rules can give has to be in REFUSALS: one missing is a refusal no log line can ever name.
names = {value for name, value in vars(rules).items()
         if name.isupper() and isinstance(value, str) and not name.startswith("_")}
told = set(rules.REFUSALS) | {rules.ON_GROUND}
ends = {rules.MANTLE, rules.LANDED, rules.GAME_MOVE, rules.JUMP, rules.WALL_LOST, rules.STICK, rules.CAMERA,
        rules.HEIGHT, rules.BLOCKED}
check("every refusal is ranked, so every refusal can be told", names - told - ends == set())
check("and the ranking holds no duplicate", len(rules.REFUSALS) == len(set(rules.REFUSALS)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
