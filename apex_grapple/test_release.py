"""Tests the rules that end a pull, each one against the reading that made it necessary."""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK: these rules are numbers only.
_spec = importlib.util.spec_from_file_location("release", HERE / "apex_grapple" / "release.py")
release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release)

fails: list[str] = []
SECOND = 1_000_000_000


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("close arrival leaves room for traction", release.arrival_for_shot(600, 200) == 100)
check("the configured radius still governs long shots", release.arrival_for_shot(600, 2500) == 600)
check("a small configured radius remains authoritative", release.arrival_for_shot(20, 200) == 20)
check("no discontinuity at the short-shot boundary", release.arrival_for_shot(600, 1198) == 599
      and release.arrival_for_shot(600, 1200) == 600 and release.arrival_for_shot(600, 1202) == 600)


check("a still player is caught by the set sphere", release.arrival_radius(150.0, 0.0) == 150.0)
# 2400 units a second at the game's frame rate is 190 units between two frames.
check("a fast player's sphere covers his stride", release.arrival_radius(150.0, 190.0) > 190.0)
check("inside the sphere is arrived", release.arrived(100.0, 150.0, 0.0))
check("outside it is not", not release.arrived(400.0, 150.0, 0.0))
check("a player who covers 190 units a frame no longer steps over the sphere",
      release.arrived(200.0, 150.0, 190.0))
check("and at a walk that same distance is not an arrival", not release.arrived(200.0, 150.0, 10.0))

check("leaving the anchor after having come near it is arriving", release.passed(400.0, 200.0, 150.0))
check("but not before having come near it", not release.passed(2000.0, 1500.0, 150.0))
check("nor while still coming nearer", not release.passed(300.0, 300.0, 150.0))
# An arc swings a long way out without passing near: a version that ended one there cut the only
# move the mod exists for (Kevin, 2026-09-20).
check("a wide swing is not an arrival", not release.passed(1600.0, 670.0, 150.0))

check("a pull longer than its limit is over", release.out_of_time(int(0.6 * SECOND), 0.5))
check("a shorter one is not", not release.out_of_time(int(0.4 * SECOND), 0.5))
check("a limit of zero is no limit", not release.out_of_time(int(60 * SECOND), 0.0))

check("covering nothing at speed is hitting something", release.blocked((2000.0, 0.0, 0.0), 2.0, 0.05))
check("covering what was asked is not", not release.blocked((2000.0, 0.0, 0.0), 100.0, 0.05))
check("grazing a wall still counts as moving", not release.blocked((2000.0, 0.0, 0.0), 60.0, 0.05))
check("a frame that asked for almost nothing proves nothing",
      not release.blocked((10.0, 0.0, 0.0), 0.0, 0.05))

check("the first moments of a pull are the take-off", release.taking_off(int(0.1 * SECOND), 0.35))
check("and later ones are not", release.taking_off(int(0.5 * SECOND), 0.35) is False)
check("a take-off time of zero means none at all", not release.taking_off(0, 0.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
