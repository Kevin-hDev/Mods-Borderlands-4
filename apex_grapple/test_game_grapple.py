"""Tests the prototype switch: the mod's point kept where it would grapple, and away where it would punch."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import game, game_grapple, game_target  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


placed: list = []
game_target.follow = lambda character, spot: placed.append(spot)
game_target.held_list = lambda: []

player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
kismet = state["kismet"]
MS = 1_000_000

game_grapple.ON = True
game_grapple.reset()
kismet.hit = (800.0, "StaticMeshActor")
game_grapple.aim_target(player, 0)
check("a wall in range gets the point", placed and placed[-1] is not None)

# The punch survives on enemies; identified nearby walls remain grappleable.
kismet.hit = (800.0, "BPChar_Enemy_Ripper")
game_grapple.aim_target(player, 60 * MS)
check("an enemy sends the point away, so the key punches", placed[-1] is None)
kismet.hit = (90.0, "StaticMeshActor")
game_grapple.aim_target(player, 120 * MS)
check("a nearby wall keeps its grapple point", placed[-1] == (90.0, 0.0, 160.0))
kismet.hit = None
game_grapple.aim_target(player, 180 * MS)
check("and so does the empty sky", placed[-1] is None)

# Sampled, not run at every frame.
placed.clear()
kismet.hit = (800.0, "StaticMeshActor")
game_grapple.aim_target(player, 1000 * MS)
game_grapple.aim_target(player, 1010 * MS)
game_grapple.aim_target(player, 1020 * MS)
check("three frames within 50 ms move the point once", len(placed) == 1)

placed.clear()
game_grapple.ON = False
game_grapple.aim_target(player, 5000 * MS)
check("switched off, the prototype places nothing", not placed)
game_grapple.ON = True

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
