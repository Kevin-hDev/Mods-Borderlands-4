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


def sample(velocity, sprinting=False, in_air=False, aiming=False, held=False):
    return Sample(sprinting, False, in_air, False, abs(velocity[0]), aiming, False, velocity, held)


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

# The far distance (104 back): aiming brings it to the game's aim camera, and it comes back while the game zooms out,
# in one move with it, not after (Kevin, 2026-10-11).
FAR = -104.0


def run_far(camera, the_sample, frames, now):
    out = None
    for _ in range(frames):
        now += FRAME_NS
        out = camera.step((0.0, 0.0), the_sample, 0.0, 0.0, now, FAR)
    return out, now


camera.reset()
out, now = run_far(camera, sample((0.0, 0.0, 0.0)), 5, 0)
check("the far distance at once on entering", out is not None and abs(out[0] - FAR) < 0.01)
out, now = run_far(camera, sample((0.0, 0.0, 0.0), aiming=True, held=True), 60, now)
check("aiming: back to the aim camera", out is None)
out, now = run_far(camera, sample((0.0, 0.0, 0.0), aiming=True), 6, now)
check("the game zooming out: the distance already comes back", out is not None and out[0] < -10.0)
out, now = run_far(camera, sample((0.0, 0.0, 0.0), aiming=True), 60, now)
check("and reaches it during the zoom-out", out is not None and abs(out[0] - FAR) < 0.5)

# An automatic distance move glides over its own, longer time (camera_distance_follow.py).
CLOSE = 76.0
moves = []
for glide_s in (0.25, 0.5):
    camera.reset()
    now = FRAME_NS
    camera.step((0.0, 0.0), sample((0.0, 0.0, 0.0)), 0.0, 0.0, now, 0.0, glide_s)
    for _ in range(9):
        now += FRAME_NS
        out = camera.step((0.0, 0.0), sample((0.0, 0.0, 0.0)), 0.0, 0.0, now, CLOSE, glide_s)
    moves.append(out[0])
check("a longer glide moves the distance slower", 0.0 < moves[1] < moves[0] < CLOSE)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
