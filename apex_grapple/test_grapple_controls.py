"""Tests ground contact, punch priority, key release, and retained speed."""

import sys

from grapple_fixture import check, fails, fresh, fly, game, grapple, sdk_stubs, settings, state, SECOND


# Landing, and the take-off before it. Eight pulls were cut at 0.06 s in game on 2026-09-20 because
# the player was still standing when the first pull frame ran: the ground has to mean nothing until
# he has had time to leave it.
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
rope.update(player, int(0.25 * SECOND))
check("standing at the start of a pull does not end it", rope.holds)
check("and the pull gives the upward speed needed to leave the floor",
      game.velocity(player.CharacterMovement)[2] >= settings.takeoff_lift.value - 1.0)
check("and the player is put back in the air, the game having walked him again",
      player.CharacterMovement.modes == [grapple.MOVE_FALLING, grapple.MOVE_FALLING])
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
rope.update(player, int(0.6 * SECOND))
check("once the take-off time is past, touching the ground ends the pull", not rope.busy)
check("and the distance covered is written down", any("moved" in line for line in state["misc"]))

settings.ground_grace.value = 0.0
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
rope.update(player, int(0.25 * SECOND))
check("a take-off time of zero ends a pull on the ground at once, as the first version did",
      not rope.busy)
settings.ground_grace.value = 0.35

settings.release_on_landing.value = False
player, rope = fresh(hit=(9000.0, "StaticMeshActor"))
rope.fire(player, 0)
rope.update(player, int(1.8 * SECOND))
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
fly(player, rope, 1.8, 2.4)
check("turned off in the menu, the ground no longer ends it", rope.holds)
settings.release_on_landing.value = True

# The key.
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
rope.key_up(int(0.25 * SECOND))
check("letting the key go lets the rope go", not rope.busy)
# A tap is what a player does by default: the key comes up long before the hook lands.
player, rope = fresh()
rope.fire(player, 0)
rope.key_up(int(0.05 * SECOND))
rope.update(player, int(0.2 * SECOND))
check("a tap still gives a whole pull, the key having come up before the hook landed", rope.holds)
rope.key_up(int(0.3 * SECOND))
check("and letting the key go once it holds still ends it", not rope.busy)

settings.release_on_key_up.value = False
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
rope.key_up(int(0.25 * SECOND))
check("turned off, the pull holds on after the key comes up", rope.holds)
settings.release_on_key_up.value = True

# A second press.
player, rope = fresh()
rope.fire(player, 0)
check("a second press during the flight calls the shot off", rope.fire(player, int(0.05 * SECOND)))
check("and leaves nothing running", not rope.busy)
check("it is written down", any("shot called off" in line for line in state["misc"]))

# What the shot refuses.
player, rope = fresh(hit=(800.0, "BPChar_Enemy_Ripper"))
check("a shot at an enemy is left to the game, which punches", not rope.fire(player, 0))
check("and nothing starts", not rope.busy)

player, rope = fresh(hit=None)
check("a shot at nothing is left to the game too", not rope.fire(player, 0))

player, rope = fresh(hit=(50.0, "StaticMeshActor"))
check("a known surface right under the nose starts a grapple", rope.fire(player, 0) and rope.busy)

# The speed carried at contact is kept on top of the pull's own cap.
player, rope = fresh(on_ground=False)
settings.pull_speed_cap.value = 500
player.CharacterMovement.Velocity = sdk_stubs.vector(400.0, 0.0, 0.0)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
for tick in range(20, 300):
    rope.update(player, int(tick / 100 * SECOND))
    if not rope.busy:
        break
check("the pull adds its cap on top of the speed already carried",
      895.0 <= game.velocity(player.CharacterMovement)[0] <= 905.0)
settings.pull_speed_cap.value = 2500

# The lift never slows a player already rising: a grapple fired out of a jump keeps its climb.
player, rope = fresh()
player.CharacterMovement.Velocity = sdk_stubs.vector(0.0, 0.0, 900.0)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
check("a player already going up faster keeps his own speed",
      game.velocity(player.CharacterMovement)[2] >= 900.0)

settings.takeoff_lift.value = 0
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
check("a lift of zero gives none, and the pull drags along the floor",
      game.velocity(player.CharacterMovement)[2] < 100.0)
settings.takeoff_lift.value = 400

# The rope's tilt is written down: it is the only line that says what was really aimed at.
player, rope = fresh()
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
check("the rope's tilt is written with the hook", any("degrees" in line for line in state["misc"]))

# Something solid in the way: the mod owns the velocity, so it must notice when the player stops
# covering the ground it gives him, or it would hold him pressed into a wall for ever.
player, rope = fresh(hit=(9000.0, "StaticMeshActor"))
rope.fire(player, 0)
rope.update(player, int(1.8 * SECOND))
fly(player, rope, 1.8, 2.6)
check("a pull that moves freely goes on", rope.holds)
for step in range(4):
    rope.update(player, int((2.6 + step * 0.05) * SECOND))
check("a player who stops covering ground has hit something, and is let go", not rope.busy)
check("and the reason says so", any("hit something" in line for line in state["misc"]))

player, rope = fresh()
rope.fire(player, 0)
rope.reset()
check("a reset rope holds nothing", not rope.busy and not rope.holds)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
