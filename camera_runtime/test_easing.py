"""The dynamic camera's smoothing: no jolt at the start, 95 % in the seconds asked, snaps when settled, long frames
clamped, several values eased together."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.easing import MAX_STEP_S, Easing  # noqa: E402

fails = []
FRAME_S = 1 / 60


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


easing = Easing(1, 1e-3)
trace = [easing.step((10.0,), 0.4, FRAME_S)[0] for _ in range(24)]
check("95 % of the way in the seconds asked", 9.4 < trace[-1] < 9.7)
check("no jolt: the first frame moves about a hundredth, then more each frame",
      trace[0] < 0.2 and trace[1] - trace[0] > trace[0] and trace[2] - trace[1] > trace[1] - trace[0])
for _ in range(120):
    easing.step((10.0,), 0.4, FRAME_S)
check("then it snaps exactly to the goal", easing.value == (10.0,))
easing.reset()
easing.step((10.0,), 0.4, 10.0)
moved = easing.value[0]
easing.reset()
easing.step((10.0,), 0.4, MAX_STEP_S)
check("a long frame moves no more than the longest step", moved == easing.value[0])
easing.step((10.0,), 0.4, -1.0)
check("a step back in time moves nothing", moved == easing.value[0])
pair = Easing(3, 0.01)
pair.snap((1.0, 2.0, 3.0))
check("snap places every value at once", pair.value == (1.0, 2.0, 3.0))
pair.step((1.0, 2.0, 30.0), 0.6, FRAME_S)
check("values ease together and each on its own", pair.value[:2] == (1.0, 2.0) and 3.0 < pair.value[2] < 4.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
