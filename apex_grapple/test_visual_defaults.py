"""Retiring investigation modes preserves the accepted hands, beam and pull."""

import sys
import types

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import game, grapple, rope_visuals, settings

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the investigation selector is no longer a setting", not hasattr(settings, "visual_diagnostic"))
check("the saved settings list no longer exposes it",
      all(option.identifier != "visual_diagnostic" for option in settings.ALL))
velocities = []
for old_value in (1, 2, 3):
    # Simulate an obsolete persisted option: it must never remove the hands or the rope.
    settings.visual_diagnostic = types.SimpleNamespace(value=old_value)
    rope_visuals.reset()
    player = sdk_stubs.FakeCharacter()
    hands = sdk_stubs.FakeArms(player)
    state["anim_instances"] = [hands]
    state["pc"] = sdk_stubs.player(player, state["mappings"])
    state["kismet"].hit = (2000.0, "StaticMeshActor")
    game.refresh(old_value, at_once=True)
    settings.show_rope.value = True
    before = len(state["niagara"].spawned)
    destroyed = len(state["destroyed"])
    rope = grapple.Rope()
    check(f"old value {old_value}: the shot starts", rope.fire(player, 0))
    check(f"old value {old_value}: both visuals start",
          len(hands.played) == 1 and len(state["niagara"].spawned) - before == 1)
    settings.show_rope.value = False
    written_before = len(state["niagara"].set)
    rope.update(player, 500_000_000)
    rope.update(player, 550_000_000)
    check(f"old value {old_value}: hand stays held", len(hands.played) == 2)
    check(f"old value {old_value}: current shot follows despite menu edit",
          len(state["niagara"].set) > written_before)
    speed = player.CharacterMovement.Velocity
    velocities.append((speed.X, speed.Y, speed.Z))
    rope.let_go("cancelled", 600_000_000)
    check(f"old value {old_value}: both visuals stop",
          len(state["destroyed"]) - destroyed == 1 and len(hands.stopped) == 1)
check("obsolete diagnostic values cannot change pulling", velocities[0] == velocities[1] == velocities[2])
del settings.visual_diagnostic

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
