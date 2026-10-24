"""The played body remembered between animation updates: every update from its holder, its own included, is always
checked, any other one asks the game only once the played body has been quiet for RECENT_NS."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.played_body import RECENT_NS, PlayedBody  # noqa: E402


def thing(address, outer=None):
    return types.SimpleNamespace(_get_address=lambda: address, Outer=outer)


MESH, ENEMY_MESH = thing(100), thing(300)
PLAYED, ENEMY, SAME_MESH = thing(10, MESH), thing(30, ENEMY_MESH), thing(11, MESH)
NO_OUTER = thing(40)
T = 5_000_000_000

failures = []


def check(name, condition):
    if not condition:
        failures.append(name)


def asks(played, obj, now_ns):
    return played.must_ask(obj, now_ns)


fresh = PlayedBody()
check("a body never found asks the game, whatever the clock",
      asks(fresh, ENEMY, T) and asks(fresh, PLAYED, T) and asks(fresh, ENEMY, 1))

played = PlayedBody()
played.remember(10, 100, T)
check("the played body's own update is checked every time", asks(played, PLAYED, T + 1))
check("another body's update asks nothing while the played body is recent", not asks(played, ENEMY, T + 1))
check("an object without outer asks nothing while the played body is recent", not asks(played, NO_OUTER, T + 1))
check("a body on the played body's mesh is checked", asks(played, SAME_MESH, T + 1))
check("still quiet just under the window", not asks(played, ENEMY, T + RECENT_NS - 1))
check("asks again once the played body is quiet for the whole window", asks(played, ENEMY, T + RECENT_NS))

played.remember(10, 100, T + RECENT_NS)
check("a new update of the played body opens the window again", not asks(played, ENEMY, T + RECENT_NS + 1))

played.forget()
check("a forgotten body asks the game again", asks(played, ENEMY, T + RECENT_NS + 2))

check("the window is longer than a frame at 20 images a second", RECENT_NS >= 50_000_000)
check("the window stays short, so a change of character is caught within 50 ms", RECENT_NS <= 50_000_000)

for name in failures:
    print("ECHEC:", name)
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
raise SystemExit(1 if failures else 0)
