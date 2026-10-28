"""Tests played_body.py: every update from the player's mesh, the player's own included, is checked against the game;
any other one asks the game only once the player's body has been quiet for RECENT_NS."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_grapple.played_body import RECENT_NS, PlayedBody, address  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def thing(where: int, outer=None):
    return types.SimpleNamespace(_get_address=lambda: where, Outer=outer)


MESH, ENEMY_MESH = thing(100), thing(300)
PLAYER, ENEMY, SAME_MESH = thing(10, MESH), thing(30, ENEMY_MESH), thing(11, MESH)
NO_OUTER = thing(40)
T = 5_000_000_000

check("an address is the game's, and nothing is 0", address(PLAYER) == 10 and address(None) == 0)

fresh = PlayedBody()
check("a body never found asks the game, whatever the clock",
      fresh.must_ask(ENEMY, T) and fresh.must_ask(PLAYER, T) and fresh.must_ask(ENEMY, 1))

played = PlayedBody()
played.remember(10, 100, T)
check("the player's own update is checked every time", played.must_ask(PLAYER, T + 1))
check("another body's update asks nothing while the player's is recent", not played.must_ask(ENEMY, T + 1))
check("an object without outer asks nothing while the player's body is recent", not played.must_ask(NO_OUTER, T + 1))
check("a new body on the player's mesh is checked", played.must_ask(SAME_MESH, T + 1))
check("still quiet just under the window", not played.must_ask(ENEMY, T + RECENT_NS - 1))
check("asks again once the player's body is quiet for the whole window", played.must_ask(ENEMY, T + RECENT_NS))

played.remember(10, 100, T + RECENT_NS)
check("a new update of the player's body opens the window again", not played.must_ask(ENEMY, T + RECENT_NS + 1))

played.forget()
check("a forgotten body asks the game again", played.must_ask(ENEMY, T + RECENT_NS + 2))

check("the window is longer than a frame at 20 images a second", RECENT_NS >= 50_000_000)
check("and stays short, so a change of character is caught within 50 ms", RECENT_NS <= 50_000_000)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
