"""Camera motion: the camera reacts late to changes of speed and comes back; standing still, a faint drift; the
strength scales it; aiming or switched off, it eases away."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import camera_motion as cm  # noqa: E402
from apex_camera_runtime.camera_motion import Motion, to_camera  # noqa: E402
from apex_camera_runtime.player_sample import Sample  # noqa: E402

fails = []
FRAME_S = 1 / 60


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def sample(velocity, in_air=False, aiming=False):
    return Sample(False, False, in_air, False, math.sqrt(sum(v * v for v in velocity)), aiming, False, velocity)


def run(motion, velocity, seconds, strength=1.0, in_air=False, aiming=False, yaw=0.0, trace=None):
    for _ in range(round(seconds * 60)):
        out = motion.step(strength, sample(velocity, in_air, aiming), 0.0, yaw, FRAME_S)
        if trace is not None:
            trace.append(out)
    return motion.output.value


def near(values, targets, tolerance=1e-6):
    return all(abs(a - b) < tolerance for a, b in zip(values, targets))


check("forward, right and up of a level camera facing X", near(to_camera((1, 0, 0), 0, 0), (1, 0, 0))
      and near(to_camera((0, 1, 0), 0, 0), (0, 1, 0)) and near(to_camera((0, 0, 1), 0, 0), (0, 0, 1)))
check("turned 90 degrees, the world's X is on the camera's left", near(to_camera((1, 0, 0), 0, 90), (0, -1, 0)))
check("looking down 90 degrees, the world's down is forward", near(to_camera((0, 0, -1), -90, 0), (1, 0, 0)))
check("limits per axis", cm.clamp((100.0, -100.0, 5.0)) == (cm.LIMITS[0], -cm.LIMITS[1], 5.0))

motion = Motion()
run(motion, (1269.0, 0.0, 0.0), 1.0)
check("already running when it starts: no lag", near(motion.output.value, (0, 0, 0), 0.01))

motion = Motion()
run(motion, (0.0, 0.0, 0.0), 0.5)
start = []
run(motion, (801.0, 0.0, 0.0), 0.2, trace=start)
check("a sprint's start (801 at once): the camera lags back, eased with no jolt",
      start[0][0] > -2.0 and start[5][0] < -5.0 and min(out[0] for out in start) >= -cm.LIMITS[0])
run(motion, (801.0, 0.0, 0.0), 2.0)
check("then it comes back while the run goes on", near(motion.output.value, (0, 0, 0), 0.05))
stop = []
run(motion, (0.0, 0.0, 0.0), 0.3, trace=stop)
check("stopping: the camera goes on a little forward", max(out[0] for out in stop) > 5.0)

motion = Motion()
run(motion, (0.0, 0.0, -1500.0), 0.5, in_air=True)
landing = []
run(motion, (0.0, 0.0, 0.0), 0.3, trace=landing)
check("landing after a fall: the camera dips, within its limit",
      -cm.LIMITS[2] - 1e-9 <= min(out[2] for out in landing) < -10.0)

motion = Motion()
run(motion, (0.0, 0.0, 0.0), 0.9)
check("standing still under a second: no drift", near(motion.output.value, (0, 0, 0), 0.01))
drift = []
run(motion, (0.0, 0.0, 0.0), 10.0, trace=drift)
sideways = [out[1] for out in drift[-300:]]
check("then a faint slow drift, right and left, never past its amplitude",
      max(sideways) > 1.0 and min(sideways) < -1.0 and max(abs(out[1]) for out in drift) <= cm.IDLE_AMPLITUDE[0])
check("the drift is slow: no frame moves it by more than a tenth of a unit",
      max(abs(b[1] - a[1]) for a, b in zip(drift, drift[1:])) < 0.1)
run(motion, (0.0, 0.0, 0.0), 0.5, aiming=True)
check("aiming takes everything away", near(motion.output.value, (0, 0, 0), 0.01))

strong, soft = Motion(), Motion()
for motion, strength in ((strong, 2.0), (soft, 0.5)):
    run(motion, (0.0, 0.0, 0.0), 0.5, strength=strength)
    run(motion, (801.0, 0.0, 0.0), 0.1, strength=strength)
check("the strength scales the motion", strong.output.value[0] < 2 * soft.output.value[0] < 0)
run(strong, (801.0, 0.0, 0.0), 1.0, strength=0.0)
check("switched off, it eases back to nothing", near(strong.output.value, (0, 0, 0), 0.01))
check("no player read, nothing", Motion().step(1.0, None, 0.0, 0.0, FRAME_S) == (0.0, 0.0, 0.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
