"""Framing by action: the offset each action asks for, the run following the speed down, the strength, the
vehicle's speed share."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import action_framing as af  # noqa: E402
from apex_camera_runtime.player_sample import Sample  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def sample(sprinting=False, sliding=False, in_air=False, crouched=False, aiming=False, flat=0.0):
    return Sample(sprinting, sliding, in_air, sliding, flat, aiming, crouched, (flat, 0.0, 0.0))


check("standing still asks for nothing", af.target(sample(), 1.0) == (0.0, 0.0) and af.action(sample()) == "rest")
check("running at full speed: further back", af.target(sample(sprinting=True, flat=1269.0), 1.0) == af.RUN)
check("running slower follows the speed down",
      math.isclose(af.target(sample(sprinting=True, flat=475.0), 1.0)[0], af.RUN[0] / 2))
check("a slide counts as running though crouched", af.action(sample(sliding=True, crouched=True)) == "run")
check("in the air: back and up", af.target(sample(in_air=True), 1.0) == af.AIR)
check("crouched: closer", af.target(sample(crouched=True), 1.0) == af.CROUCH)
check("the air wins over running", af.action(sample(sprinting=True, in_air=True)) == "air")
check("aiming wins over everything, asks for nothing and eases out faster",
      af.action(sample(sprinting=True, in_air=True, aiming=True)) == "aim"
      and af.target(sample(aiming=True), 1.0) == (0.0, 0.0) and af.seconds(sample(aiming=True)) == af.AIM_SECONDS)
check("no player, nothing", af.action(None) == "none" and af.target(None, 1.0) == (0.0, 0.0))
check("the strength scales it: 50 % is half, 0 is nothing",
      af.target(sample(in_air=True), 0.5) == (af.AIR[0] / 2, af.AIR[1] / 2)
      and af.target(sample(in_air=True), 0.0) == (0.0, 0.0))
check("at the wheel, standing still asks for nothing", af.vehicle_target(0.0, 0.0, 1.0) == (0.0, 0.0))
check("at the wheel, full from the floor while the top seen is low", af.vehicle_target(1000.0, 1200.0, 1.0) == af.VEHICLE)
check("at the wheel, full from 0.75 of the top seen, following the speed down",
      af.vehicle_target(1500.0, 2000.0, 1.0) == af.VEHICLE
      and math.isclose(af.vehicle_target(750.0, 2000.0, 1.0)[0], af.VEHICLE[0] / 2))
check("at the wheel, the strength scales it", af.vehicle_target(5000.0, 5000.0, 1.5)[0] == af.VEHICLE[0] * 1.5)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
