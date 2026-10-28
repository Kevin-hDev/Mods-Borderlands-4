"""Tests look_sight.py: a rope in front shows; one beside the view, above it or behind the camera does not; one whose
two ends are off screen but that runs across it shows; a rope passing from behind the camera to in front shows;
a turned camera sees by its own axes."""

import importlib.util
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK: the sight is numbers only.
_spec = importlib.util.spec_from_file_location("look_sight", HERE / "apex_grapple" / "look_sight.py")
sight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sight)

fails = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


# Kevin's view: 110 degrees across, 16:9.
ACROSS = math.tan(math.radians(55.0))
UP = ACROSS * 9.0 / 16.0
EYE = (0.0, 0.0, 0.0)
AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def shows(*points, eye=EYE, axes=AXES):
    return sight.shows(eye, axes, ACROSS, UP, list(points))


check("a rope straight ahead shows", shows((100.0, 0.0, 0.0), (500.0, 0.0, 0.0)))
check("a rope whose two ends are off screen, left and right, but that runs across it shows",
      shows((100.0, 500.0, 0.0), (100.0, -500.0, 0.0)))
check("a rope behind the camera does not show", not shows((-100.0, 0.0, 0.0), (-500.0, 10.0, 0.0)))
check("a rope off to the left does not show", not shows((100.0, 300.0, 0.0), (500.0, 1000.0, 0.0)))
check("a rope above the view does not show", not shows((100.0, 0.0, 200.0), (1000.0, 0.0, 1000.0)))
check("a rope from a hand out at the bottom left to an anchor out at the top left does not show",
      not shows((30.0, 60.0, -60.0), (300.0, 600.0, 800.0)))
check("a rope from a hand out at the bottom left to an anchor out at the top right shows",
      shows((30.0, 60.0, -60.0), (300.0, -600.0, 800.0)))
check("a rope passing from behind the camera to in front of it shows", shows((-100.0, 0.0, 0.0), (100.0, 0.0, 0.0)))
check("a rope just under the bottom edge does not show, just above it does",
      not shows((100.0, 0.0, -UP * 100.0 - 1.0), (400.0, 0.0, -UP * 400.0 - 1.0))
      and shows((100.0, 0.0, -UP * 100.0 + 1.0), (400.0, 0.0, -UP * 400.0 + 1.0)))
check("a curved rope whose middle comes into view shows, though both its ends are off it",
      shows((100.0, 300.0, 0.0), (300.0, 0.0, 0.0), (100.0, -300.0, 0.0)))
check("a rope cutting past the view's top left corner, outside it, does not show",
      not shows((100.0, 200.0, 50.0), (100.0, 50.0, 200.0)))
check("a single point is no rope", not shows((100.0, 0.0, 0.0)))
turned = ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
check("a camera turned round sees what is before it by its own axes, not what is behind it",
      shows((500.0, 0.0, 0.0), (0.0, 0.0, 0.0), eye=(1000.0, 0.0, 0.0), axes=turned)
      and not shows((1500.0, 0.0, 0.0), (2000.0, 0.0, 0.0), eye=(1000.0, 0.0, 0.0), axes=turned))

print(f"RESULTAT: {'TOUS LES TESTS PASSENT' if not fails else f'{len(fails)} ECHEC(S)'}")
raise SystemExit(1 if fails else 0)
