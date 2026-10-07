"""Close, normal and far in turn; normal is the game's camera; a key press glides, entering third person does not,
and aiming gives the game's aim camera back."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import camera_distance  # noqa: E402
from apex_camera_runtime.camera_distance import CLOSE, FAR, NORMAL, following, offset  # noqa: E402
from apex_camera_runtime.dynamic_camera import DynamicCamera  # noqa: E402
from apex_camera_runtime.player_sample import Sample  # noqa: E402

fails = []
FRAME_NS = 16_666_667
STILL = Sample(False, False, False, False, 0.0, False)
AIMING = Sample(False, False, False, False, 0.0, True)


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def run(camera, distance, sample, frames, now):
    out = None
    for _ in range(frames):
        now += FRAME_NS
        out = camera.step((0.0, 0.0), sample, 0.0, 0.0, now, distance)
    return out, now


check("one press goes close, normal, far, then close again",
      (following(CLOSE), following(NORMAL), following(FAR)) == (NORMAL, FAR, CLOSE))
check("a hand-edited value starts over from normal", all(following(bad) == NORMAL for bad in (None, True, -1, 3, 1.0)))
check("normal adds nothing: the game's own camera", offset(NORMAL) == 0.0)
check("close comes forward, far goes back", offset(CLOSE) > 0.0 > offset(FAR))
check("a hand-edited value is the game's camera", offset("far") == 0.0 and offset(True) == 0.0)

camera = DynamicCamera()
out, now = run(camera, offset(FAR), STILL, 1, 0)
check("entering third person puts the camera at its distance at once", out == (offset(FAR), 0.0, 0.0))
out, now = run(camera, offset(CLOSE), STILL, 3, now)
check("a press glides instead of jumping", out is not None and offset(FAR) < out[0] < offset(CLOSE))
frames = round(camera_distance.SECONDS / (FRAME_NS / 1e9))
out, now = run(camera, offset(CLOSE), STILL, frames, now)
check("the glide ends within its seconds",
      out is not None and abs(out[0] - offset(CLOSE)) < 0.05 * (offset(CLOSE) - offset(FAR)))
out, now = run(camera, offset(CLOSE), AIMING, 60, now)
check("aiming gives the game's aim camera back", out is None)
out, now = run(camera, offset(CLOSE), STILL, 60, now)
check("after aiming the distance comes back", out == (offset(CLOSE), 0.0, 0.0))
out, now = run(camera, offset(NORMAL), STILL, 60, now)
check("back to normal: nothing written", out is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
