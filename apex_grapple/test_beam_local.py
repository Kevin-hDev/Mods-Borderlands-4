"""Catches world coordinates fed to a local beam, a frozen origin, and visual failures stopping pulls."""

import math
import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import beam, game, game_grapple, grapple, report

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
niagara = state["niagara"]
beam.start(player, (1000.0, 0.0, 300.0))
component = beam._component
beam.follow((-198000.0, 326000.0, 300.0), (-197700.0, 326400.0, 300.0))
ends = {name: (value.X, value.Y, value.Z) for name, value in niagara.set[-2:]}
check("a 3-4-5 rope far from the map origin writes length 500", ends.get("Target") == (500.0, 0.0, 0.0))
check("the source is the component origin", ends.get("Source") == (0.0, 0.0, 0.0))
check("the component follows the hand", getattr(component, "world_spot", None) == (-198000.0, 326000.0, 300.0))
turn = getattr(component, "world_turn", None)
check("the local X axis points along the 3-4-5 rope", turn is not None and abs(turn[1] - 53.130102) < 0.00001)

beam.follow((0.0, 1000.0, 0.0), (0.0, 0.0, 0.0))
turn = getattr(component, "world_turn", None)
check("rotation also changes after the first frame", turn is not None and turn == (0.0, -90.0, 0.0))
check("activation is not restarted at each frame", getattr(component, "activations", 0) == 1)
beam.follow((0.0, 0.0, math.nan), (1.0, 0.0, 0.0))
check("invalid geometry disables the visual", beam._broken and beam._component is None)
check("invalid geometry cleans up the existing component", component in state["destroyed"])

beam.reset()
report.reset()
state["errors"].clear()
state["kismet"].hit = (2000.0, "StaticMeshActor")
rope = grapple.Rope()
rope.fire(player, 0)
component = beam._component
player.location = sdk_stubs.vector(100.0, 200.0, 100.0)
rope.update(player, 100_000_000)
check("the rope origin follows the player while the hook still flies",
      component.world_spot == (100.0, 230.0, 135.0))


def refused(*args):
    raise RuntimeError("pose refused")


component.K2_SetWorldLocationAndRotation = refused
rope.update(player, 500_000_000)
rope.update(player, 550_000_000)
rope.update(player, 600_000_000)
check("a failed visual leaves the real pull holding", rope.holds)
check("and the pull still writes speed", player.CharacterMovement.Velocity.X > 0)
check("the failed component is cleaned up", component in state["destroyed"])
check("the visual error is written once with its exception", sum("RuntimeError('pose refused')" in line for line in state["errors"]) == 1)

placed = []
game_grapple.game_target.follow = lambda character, spot: placed.append(spot)
game_grapple.aim_target(player, 1_000_000_000)
check("the local beam trial does not place a native target", not placed)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
