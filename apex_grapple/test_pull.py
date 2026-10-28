"""Tests the model: the two accelerations, their speed caps, and a whole second replayed against Titanfall 2."""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK installed: pull.py must stay free of
# the game, and a plain import of the package would hide that by loading the SDK-bound modules too.
_spec = importlib.util.spec_from_file_location("pull", HERE / "apex_grapple" / "pull.py")
pull = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pull)

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(got: float, wanted: float, margin: float = 0.5) -> bool:
    return abs(got - wanted) <= margin


check("a direction comes back with a length of one", near(sum(part ** 2 for part in pull.unit(3.0, 4.0, 0.0)), 1.0))
check("a vector of nothing has no direction", pull.unit(0.0, 0.0, 0.0) is None)
check("the rope points at the anchor", pull.toward((0.0, 0.0, 0.0), (0.0, 0.0, 10.0)) == (0.0, 0.0, 1.0))
check("standing on the anchor there is no rope", pull.toward((5.0, 5.0, 5.0), (5.0, 5.0, 5.0)) is None)
check("the distance is the distance", near(pull.distance((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)), 5.0))

up = (0.0, 0.0, 1.0)
check("speed along a way is what goes that way", near(pull.speed_along((10.0, 0.0, 300.0), up), 300.0))
check("going the other way reads as negative", near(pull.speed_along((0.0, 0.0, -300.0), up), -300.0))

# Acceleration x time, and nothing else, while the cap is far off.
check("a push adds acceleration times the frame",
      near(pull.push_toward((0.0, 0.0, 0.0), up, 1000.0, 9999.0, 0.1)[2], 100.0))
check("it leaves the other axes alone",
      pull.push_toward((7.0, -3.0, 0.0), up, 1000.0, 9999.0, 0.1)[:2] == (7.0, -3.0))
check("at the cap it adds nothing at all",
      pull.push_toward((0.0, 0.0, 500.0), up, 1000.0, 500.0, 0.1)[2] == 500.0)
check("past the cap it does not pull the speed back down",
      pull.push_toward((0.0, 0.0, 900.0), up, 1000.0, 500.0, 0.1)[2] == 900.0)
check("the last frame before the cap adds only what is left",
      near(pull.push_toward((0.0, 0.0, 450.0), up, 1000.0, 500.0, 0.1)[2], 500.0))
check("the speed already carried the other way is counted in",
      near(pull.push_toward((0.0, 0.0, -200.0), up, 1000.0, 500.0, 0.1)[2], -100.0))

# A whole second of pull under Titanfall 2's gravity: 1.8 x 600 = 1080, the 1060 measured in game.
# The rope carries the weight in every check below, so that each term is read on its own.
speed, here, anchor = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 10000.0)
for _ in range(100):
    speed = pull.step(speed, here, anchor, (0.0, 0.0, 0.0), 600.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 0.01)
check("a second of pull under Titanfall's gravity gives the 1080 the model says", near(speed[2], 1080.0, 1.0))

speed = (0.0, 0.0, 0.0)
for _ in range(100):
    speed = pull.step(speed, here, anchor, (0.0, 0.0, 0.0), 600.0, 1.8, 2500.0, 1.0, 650.0, 1.0, 0.01)
check("the pull never goes past its own cap", speed[2] <= 2500.0)

# The stick pushes sideways, in world axes, and stops at its own cap.
speed = (0.0, 0.0, 0.0)
for _ in range(200):
    speed = pull.step(speed, here, anchor, (1.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 1.0, 650.0, 1.0, 0.01)
check("the stick alone pushes the way it is pushed", near(speed[0], 650.0, 1.0))
check("and stops dead at its cap, it does not creep past it", speed[0] <= 650.0)
check("the stick alone never touches the height", speed[2] == 0.0)

check("a stick at rest pushes nothing",
      pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 1.0, 650.0, 1.0, 0.1) ==
      (0.0, 0.0, 0.0))
half = pull.step((0.0, 0.0, 0.0), here, anchor, (0.5, 0.0, 0.0), 980.0, 0.0, 9999.0, 1.0, 650.0, 1.0, 0.01)
full = pull.step((0.0, 0.0, 0.0), here, anchor, (1.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 1.0, 650.0, 1.0, 0.01)
check("a stick pushed half way pushes half as hard", near(half[0] * 2.0, full[0], 0.01))

# The rope carries the player's weight: at 1 he flies straight along it, at 0 he falls as he would.
carried = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 0.0, 650.0, 1.0, 0.1)
check("a rope that carries him fully leaves the height alone", carried[2] == 0.0)
dropped = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 0.0, 650.0, 0.0, 0.1)
check("a rope that carries nothing lets him fall at the game's gravity", near(dropped[2], -98.0, 0.1))
half = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 0.0, 9999.0, 0.0, 650.0, 0.5, 0.1)
check("half carried is half the fall", near(half[2], -49.0, 0.1))

# A frame that lasted a second is a freeze, not a frame: taken at face value it would fire the
# player out of the level.
long_frame = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 1.0)
capped = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, pull.LONGEST_STEP_S)
check("a frozen frame counts as the longest frame allowed", long_frame == capped)
check("a frame of no time changes nothing",
      pull.step((1.0, 2.0, 3.0), here, anchor, (1.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 0.0) ==
      (1.0, 2.0, 3.0))
check("a frame of negative time changes nothing",
      pull.step((1.0, 2.0, 3.0), here, anchor, (1.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, -0.5) ==
      (1.0, 2.0, 3.0))
check("standing exactly on the anchor does not crash the pull",
      pull.step((0.0, 0.0, 0.0), here, here, (0.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 0.01) ==
      (0.0, 0.0, 0.0))

# Gravity doubled by Apex Movement: the pull follows it instead of staying behind.
light = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 980.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 0.01)
heavy = pull.step((0.0, 0.0, 0.0), here, anchor, (0.0, 0.0, 0.0), 1960.0, 1.8, 9999.0, 1.0, 650.0, 1.0, 0.01)
check("a doubled gravity doubles the pull", near(light[2] * 2.0, heavy[2], 0.01))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
