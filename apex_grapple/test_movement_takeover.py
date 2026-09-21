"""A real handover must preserve its successor's velocity and reject further pulling."""

import math
import sys
import types

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import game, grapple, settings

fails = []


def check(label, condition):
    print(("OK" if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
movement.ReplicatedMantleState = types.SimpleNamespace(ActionIndex=-1)
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["kismet"].hit = (2500, "StaticMeshActor")
game.refresh(0, at_once=True)
settings.show_rope.value = False
rules = types.SimpleNamespace(start=None)
module = types.SimpleNamespace(mod=types.SimpleNamespace(is_enabled=True),
                               game=types.SimpleNamespace(character=lambda: player),
                               wall_climb=types.SimpleNamespace(_rules=rules))
sys.modules["apex_movement"] = module

rope = grapple.Rope()
check("a wall alone does not prevent a normal shot", rope.fire(player, 0))
rope.update(player, 500_000_000)
check("the normal shot reaches its pulling phase", rope.holds)
rules.start = object()
movement.Velocity = sdk_stubs.vector(777, 22, 333)
rope.update(player, 550_000_000)
check("actual climbing ends the old pull", not rope.busy)
check("handover does not brake or replace climbing velocity",
      game.velocity(movement) == (777, 22, 333))
check("a new shot cannot override an active climb", not rope.fire(player, 600_000_000))
rules.start = None
check("a shot works again once climbing really ended", rope.fire(player, 650_000_000))
movement.ReplicatedMantleState.ActionIndex = 0
movement.Velocity = sdk_stubs.vector(333, 44, 555)
rope.update(player, 700_000_000)
check("mantling cancels even an in-flight hook", not rope.busy)
check("mantling keeps the game's own momentum", game.velocity(movement) == (333, 44, 555))

movement.ReplicatedMantleState.ActionIndex = -1
rope.reset()
settings.hook_speed.value = float("nan")
try:
    accepted = rope.fire(player, 800_000_000)
except Exception:
    accepted = False
check("invalid flight settings are repaired before a key-triggered shot",
      accepted and math.isfinite(settings.hook_speed.value))
settings.hook_speed.value = settings.hook_speed.default_value
rope.reset()
rope.fire(player, 900_000_000)
rope.update(player, 1_900_000_000)
settings.pull_strength.value = float("nan")
rope.update(player, 1_950_000_000)
check("invalid settings cannot reach velocity between two frames",
      all(math.isfinite(value) for value in game.velocity(movement)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
