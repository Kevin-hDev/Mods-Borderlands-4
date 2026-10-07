"""Each shoulder looks straight ahead, level, on the Camera channel, and refuses a result it cannot trust."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder_auto import BLOCKED, CLEAR  # noqa: E402
from apex_camera_runtime.shoulder_sight import (BLOCKED_CM, CAMERA_CHANNEL, CLEAR_CM, SIGHT_CM,  # noqa: E402
                                                 ShoulderSight, free_share)

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Sdk:
    @staticmethod
    def make_struct(name, **fields):
        return types.SimpleNamespace(name=name, **fields)


class Kismet:
    def __init__(self, hits):
        # One answer per trace: a distance, None for no hit, or a raw answer.
        self.hits = list(hits)
        self.calls = []

    def SphereTraceSingle(self, *args):
        self.calls.append(args)
        hit = self.hits.pop(0)
        if isinstance(hit, tuple):
            return hit
        if hit is None:
            return False, Sdk.make_struct("HitResult")
        return True, Sdk.make_struct("HitResult", Distance=hit)


actor = object()
kismet = Kismet([None, None])
sight = ShoulderSight(kismet, Sdk())
check("nothing ahead is fully clear", sight.share(actor, (0.0, 0.0, 100.0), 0.0) == 1.0)
first, last = kismet.calls[0][1], kismet.calls[0][2]
check("the line starts at the camera", (first.X, first.Y, first.Z) == (0.0, 0.0, 100.0))
check("the line goes straight ahead and level", math.isclose(last.X, SIGHT_CM) and last.Y == 0.0 and last.Z == 100.0)
check("the Camera channel is used, so characters are not walls", kismet.calls[0][4] == CAMERA_CHANNEL)
check("the hunter is ignored", kismet.calls[0][6] == [actor])
check("simple then detailed geometry", [call[5] for call in kismet.calls] == [False, True])

kismet = Kismet([None, None])
ShoulderSight(kismet, Sdk()).share(actor, (0.0, 0.0, 0.0), 90.0)
last = kismet.calls[0][2]
check("the camera's yaw turns the line", abs(last.X) < 1e-6 and math.isclose(last.Y, SIGHT_CM))

check("the nearest wall of the two traces counts",
      math.isclose(ShoulderSight(Kismet([600.0, 200.0]), Sdk()).share(actor, (0, 0, 0), 0.0), free_share(200.0)))
check("a wall at the swap distance is exactly the swap threshold", math.isclose(free_share(BLOCKED_CM), BLOCKED))
check("a wall at the clear distance is exactly the clear threshold", math.isclose(free_share(CLEAR_CM), CLEAR))
check("about 2.5 m ahead of a hunter 2.6 m in front of the camera is in the way",
      free_share(500.0) < BLOCKED < free_share(520.0))
check("the share grows with the distance", all(free_share(a) < free_share(b) for a, b in
                                               ((0, 100), (300, 510), (510, 600), (720, 790))))
check("the end of the line is fully clear", free_share(SIGHT_CM) == 1.0 and free_share(0.0) == 0.0)
check("a wall at the camera leaves no view", ShoulderSight(Kismet([0.0, None]), Sdk()).share(actor, (0, 0, 0), 0) == 0)

for label, answer in (("a malformed answer", ("hit",)), ("a distance past the line", 900.0),
                      ("an undefined distance", float("nan"))):
    try:
        ShoulderSight(Kismet([answer, None]), Sdk()).share(actor, (0, 0, 0), 0.0)
    except ValueError:
        refused = True
    else:
        refused = False
    check(f"{label} is refused", refused)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
