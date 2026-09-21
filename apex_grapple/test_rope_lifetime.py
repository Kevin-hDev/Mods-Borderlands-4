"""The lifetime experiment changes one effect parameter before activation, never the pull."""

import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import beam, game, grapple, settings

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["kismet"].hit = (2000.0, "StaticMeshActor")
game.refresh(0, at_once=True)
rope = grapple.Rope()
check("a shot starts", rope.fire(player, 0))
component = beam._component
check("the effect receives ten seconds before it is activated",
      getattr(component, "floats_at_activation", None) == {"User.Lifetime": 10.0})
rope.update(player, 500_000_000)
rope.update(player, 550_000_000)
check("the pull still acts", rope.holds and player.CharacterMovement.Velocity.X > 0)
check("attachment does not restart the beam", component.activations == 1)
player.location.X += 100
beam.follow(game.hand_spot(player), rope.anchor)
check("a persistent beam still follows the moving player", component.world_spot == game.hand_spot(player))
check("the experiment changes no other float parameter",
      getattr(component, "float_parameters", None) == {"User.Lifetime": 10.0})
rope.let_go("cancelled", 600_000_000)
check("release destroys the beam without waiting ten seconds", state["destroyed"] == [component])
check("the pull ends with the beam", not rope.busy)

# A rejected lifetime write must not masquerade as a successful experiment or kill the pull.
rope.reset()
state["niagara"].float_fails = True
state["errors"].clear()
check("a failed visual override still permits a shot", rope.fire(player, 1_000_000_000))
check("a failed visual override is reported", any("lifetime refused" in line for line in state["errors"]))
check("a failed visual override is discarded", beam._component is None)
rope.update(player, 1_500_000_000)
check("a failed visual override still permits attachment", rope.holds)
rope.let_go("cancelled", 1_600_000_000)
state["niagara"].float_fails = False

# The opt-out remains authoritative, including for the new parameter writer.
rope.reset()
settings.show_rope.value = False
before = len(state["niagara"].spawned)
check("the rope visibility option still permits grappling", rope.fire(player, 2_000_000_000))
check("the visibility opt-out creates no effect", len(state["niagara"].spawned) == before)
rope.let_go("cancelled", 2_100_000_000)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
