"""Checks independent axis fixtures, degenerate geometry, and invalid coordinates."""

import math
import sys

import sdk_stubs

sdk_stubs.install()
from apex_grapple import rope_pose

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


for label, hand, anchor, expected in (
    ("east", (0, 0, 0), (500, 0, 0), (0, 0)),
    ("north", (0, 0, 0), (0, 500, 0), (0, 90)),
    ("up", (0, 0, 0), (0, 0, 500), (90, 0)),
    ("down", (0, 0, 100), (0, 0, 0), (-90, 0)),
    ("zero length", (1, 1, 1), (1, 1, 1), (0, 0)),
):
    actual = rope_pose.facing(hand, anchor)
    check(label, all(math.isclose(a, e, abs_tol=0.00001) for a, e in zip(actual, expected)))

for label, spot in (("missing axis", (0, 0)), ("nan", (math.nan, 0, 0)),
                    ("infinity", (0, math.inf, 0)), ("out of range", (1e12, 0, 0))):
    refused = False
    try:
        rope_pose.facing(spot, (0, 0, 0))
    except ValueError:
        refused = True
    check(label + " is refused before a game call", refused)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
