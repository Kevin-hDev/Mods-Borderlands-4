"""Restore the pre-investigation hand pose while preserving the existing pull and beam."""

import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import animation, game, grapple

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
hands = sdk_stubs.FakeArms(player)
state["anim_instances"] = [hands]
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["kismet"].hit = (2000.0, "StaticMeshActor")
game.refresh(0, at_once=True)
rope = grapple.Rope()
check("the shot still starts", rope.fire(player, 0))
check("the initial throw montage is played", len(hands.played) == 1)
initial = dict(hands.played[0])
rope.update(player, 500_000_000)
check("the rope attaches normally", rope.holds)
check("attachment restores the established held pose", len(hands.played) == 2)
if len(hands.played) == 2:
    held = hands.played[1]
    check("the held pose uses the existing timing", held["InTimeToStartMontageAt"] ==
          game.grapple_animation().GetPlayLength() * animation.HOLD_AT)
    check("the held pose uses the existing slow rate", held["InPlayRate"] == animation.FROZEN_RATE)
    check("the held pose uses the existing blend", held["BlendInTime"] == animation.HOLD_BLEND_S)
check("the initial montage parameters are unchanged", hands.played[0] == initial)
check("attachment does not stop the arms", not hands.stopped)
check("attachment does not destroy the beam", not state["destroyed"])

rope.update(player, 550_000_000)
check("the pull still writes speed", player.CharacterMovement.Velocity.X > 0)
check("the held pose is not restarted every frame", len(hands.played) == 2)
check("holding the hands does not respawn the rope", len(state["niagara"].spawned) == 1)

rope.let_go("cancelled", 600_000_000)
check("letting go releases the pull", not rope.busy)
check("letting go still destroys the beam", len(state["destroyed"]) == 1)
check("letting go still stops the arms", len(hands.stopped) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
