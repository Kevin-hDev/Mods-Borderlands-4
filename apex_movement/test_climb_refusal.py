"""Tests the line that says why a climb did not start: the furthest reason of a flight, told once, on landing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import climb_refusal, climb_rules  # noqa: E402
from apex_movement.climb_aim import Wall  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lines() -> list[str]:
    return [line for line in state["misc"] if "wall climb refused" in line]


LIMITS = climb_rules.Limits(height=372.0, delay_ns=0, lean_deg=60.0)
WALL = Wall(distance=104.0, into_x=1.0, into_y=0.0, flat=0.99)


def moment(**changes: object) -> climb_rules.Moment:
    values: dict = dict(now_ns=0, in_air=True, on_ground=False, game_move=False, mantling=False, near_game_climb=False,
                        z=0.0, jumps=1, stick_x=1.0, stick_y=0.0, view_yaw=0.0, wall=WALL, hits=5, high_wall=True)
    values.update(changes)
    return climb_rules.Moment(**values)


climb_refusal.note(climb_rules.NO_WALL, moment(wall=None), LIMITS)
check("nothing is written while still in the air", lines() == [])
climb_refusal.note(climb_rules.TOO_FAR, moment(), LIMITS)
climb_refusal.note(climb_rules.NO_WALL, moment(wall=None), LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("landing writes one line, the furthest reason of the flight, not the last one seen",
      len(lines()) == 1 and "reason=too_far" in lines()[0])
check("with the measures of that moment and what was needed",
      "distance=104 flat=0.99 hits=5/5 stick=1.00 stick_deg=0 view_deg=0" in lines()[0]
      and "needs distance<=90 flat>=0.70 stick_deg<=60 view_deg<=45" in lines()[0])

state["misc"].clear()
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a second landing with nothing new says nothing", lines() == [])

climb_refusal.note(climb_rules.NO_WALL, moment(wall=None, hits=0, stick_x=0.3), LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("with no wall met at all, the line says so, with the traces that went through and the stick",
      len(lines()) == 1 and "reason=no_wall wall=none hits=0/5 stick=0.30" in lines()[0])

state["misc"].clear()
climb_refusal.note(climb_rules.TOO_FAR, moment(), LIMITS)
climb_refusal.started()
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a flight that ends in a climb explains nothing", lines() == [])

climb_refusal.note(climb_rules.CAMERA, moment(), LIMITS)
climb_refusal.reset()
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a reset forgets the flight", lines() == [])

climb_refusal.note(climb_rules.SLOPE, moment(wall=Wall(distance=60.0, into_x=1.0, into_y=0.0, flat=0.42)), LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a face that leaned too much is named, with how upright it stood",
      len(lines()) == 1 and "reason=slope" in lines()[0] and "flat=0.42" in lines()[0])

# A frame where the player asks for nothing never hides a real try.
state["misc"].clear()
climb_refusal.note(climb_rules.TOO_FAR, moment(), LIMITS)
climb_refusal.note(climb_rules.NO_STICK, moment(stick_x=0.0, wall=Wall(distance=53.0, into_x=1.0, into_y=0.0, flat=0.92)),
                   LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a released stick at the end of a flight does not hide the try",
      len(lines()) == 1 and "reason=too_far" in lines()[0])

state["misc"].clear()
climb_refusal.note(climb_rules.NO_STICK, moment(stick_x=0.0), LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("but a flight where the stick was never pushed still says so",
      len(lines()) == 1 and "reason=no_stick" in lines()[0])

# A refusal that beats another only when it is closer to a climb, whatever the reason.
state["misc"].clear()
climb_refusal.note(climb_rules.MANTLING, moment(), LIMITS)
climb_refusal.note(climb_rules.LOW_ONLY, moment(), LIMITS)
climb_refusal.note(climb_rules.ON_GROUND, moment(in_air=False, on_ground=True), LIMITS)
check("a wall refused for being too low beats the game being busy: it came closer to a climb",
      len(lines()) == 1 and "reason=low_only" in lines()[0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
