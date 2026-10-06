"""Framing and motion summed into one offset per frame; None once both rest at nothing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.dynamic_camera import DynamicCamera  # noqa: E402
from apex_camera_runtime.player_sample import Sample  # noqa: E402

fails = []
FRAME_NS = 16_666_667


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def sample(velocity, sprinting=False, in_air=False):
    return Sample(sprinting, False, in_air, False, abs(velocity[0]), False, False, velocity)


def run(camera, values, the_sample, frames, now):
    out = None
    for _ in range(frames):
        now += FRAME_NS
        out = camera.step(values, the_sample, 0.0, 0.0, now)
    return out, now


camera = DynamicCamera()
out, now = run(camera, (1.0, 1.0), sample((0.0, 0.0, 0.0)), 30, 0)
check("standing still at first: nothing to write", out is None)
out, now = run(camera, (1.0, 1.0), sample((1269.0, 0.0, 0.0), sprinting=True), 90, now)
check("running: the framing's back offset, the motion settled back to nothing", out is not None and out[0] < -55.0)
out, now = run(camera, (1.0, 0.0), sample((0.0, 0.0, 0.0)), 6, now)
check("the motion switched off alone leaves the framing easing", out is not None and out[0] < 0.0)
out, now = run(camera, (0.0, 0.0), sample((0.0, 0.0, 0.0)), 200, now)
check("both off: back to nothing, then None", out is None)
camera.reset()
out, _ = run(camera, (1.0, 1.0), sample((0.0, 0.0, 0.0), in_air=True), 60, 0)
check("in the air: up as well", out is not None and out[2] > 20.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
