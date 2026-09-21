"""Tests flight, steering, arrival, and duration limits."""

import sys

from grapple_fixture import check, fails, fresh, fly, game, grapple, sdk_stubs, settings, state, SECOND


player, rope = fresh(on_ground=False)
check("the rope starts at rest", not rope.busy and not rope.holds)
check("a shot at a surface takes the key", rope.fire(player, 0))
check("the hook is on its way", rope.state == grapple.FLYING)
# 1000 units at the default 5000 units a second: a fifth of a second.
check("the anchor sits where the ray stopped", rope.anchor[0] == 1000.0)

before = game.velocity(player.CharacterMovement)
rope.update(player, int(0.1 * SECOND))
check("nothing is written while the hook flies", game.velocity(player.CharacterMovement) == before)
check("and the player is left on the ground", player.CharacterMovement.modes == [])

rope.update(player, int(0.2 * SECOND))
check("at contact the rope holds", rope.holds)
check("a player already in the air is left alone: no lift, no mode written",
      player.CharacterMovement.modes == [])

rope.update(player, int(0.21 * SECOND))
speed = game.velocity(player.CharacterMovement)
# Strength x gravity x the frame, along the rope: read from the setting rather than written here, so
# that tuning the pull in game does not turn this test red for no reason.
wanted = float(settings.pull_strength.value) * 980.0 * 0.01
check("the pull pulls toward the anchor, at strength times gravity",
      abs(speed[0] - wanted) < wanted * 0.05)
check("with the stick at rest it pulls along the rope and nowhere else",
      speed[1] == 0.0 and abs(speed[2] / speed[0] - 60.0 / 1000.0) < 0.001)

player.input = sdk_stubs.vector(0.0, 1.0, 0.0)
rope.update(player, int(0.22 * SECOND))
check("the stick pushes the way it is pushed, which is what bends the path",
      game.velocity(player.CharacterMovement)[1] > 0.0)
player.input = sdk_stubs.vector(0.0, 0.0, 0.0)

# Arrival.
player.location = sdk_stubs.vector(950.0, 0.0, 160.0)
rope.update(player, int(0.23 * SECOND))
check("arriving at the anchor ends the pull", not rope.busy)
check("the aim's own pitch is written with the shot", any("aim " in line for line in state["misc"]))
check("and says so", any("let go: arrived" in line for line in state["misc"]))
kept = game.velocity(player.CharacterMovement)
rope.update(player, int(0.24 * SECOND))
check("a pull that ended writes nothing more", game.velocity(player.CharacterMovement) == kept)
check("the speed it reached is left untouched: no braking, no reset", kept[0] > 0.0)

# The arrival distance is pinned for what follows: these checks are about the rules, not about the
# value Kevin tuned, and they would go red every time he changes it.
settings.arrival_distance.value = 150

# Flying past the anchor. A sphere alone misses it: at 2400 units a second the player covers 190
# units between two frames and steps clean over a 150 unit sphere, which in game left him swinging
# back and forth through the anchor for three seconds.
player, rope = fresh(on_ground=False)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
for step, spot in enumerate([(200.0, 0.0, 160.0), (800.0, 0.0, 160.0), (1190.0, 0.0, 160.0),
                             (1600.0, 0.0, 160.0), (2000.0, 0.0, 160.0)]):
    player.location = sdk_stubs.vector(*spot)
    rope.update(player, int((0.6 + step * 0.01) * SECOND))
check("a player flying past the anchor is let go, the sphere having grown with his stride",
      not rope.busy)

# The same, but passing wide of the anchor: the sphere never catches him, the receding does.
player, rope = fresh(on_ground=False)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
state["misc"].clear()
# Small steps, 400 units to one side: the sphere never reaches him, so only the receding can end it.
for step in range(1, 16):
    player.location = sdk_stubs.vector(step * 100.0, 400.0, 160.0)
    rope.update(player, int((0.2 + step * 0.05) * SECOND))
check("a player who passes wide of the anchor is let go too", not rope.busy)
check("and the reason names it", any("passed the anchor" in line for line in state["misc"]))

player, rope = fresh(on_ground=False)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
for step, spot in enumerate([(200.0, 0.0, 160.0), (500.0, 0.0, 160.0), (700.0, 0.0, 160.0)]):
    player.location = sdk_stubs.vector(*spot)
    rope.update(player, int((0.6 + step * 0.01) * SECOND))
check("coming nearer and nearer does not end it", rope.holds)

# An arc swings a long way out without ever coming near: ending it there would kill the one move the
# mod exists for (Kevin, 2026-09-20, a first version did exactly that).
player, rope = fresh(on_ground=False)
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
for step, spot in enumerate([(400.0, 300.0, 160.0), (700.0, 700.0, 160.0), (600.0, 1200.0, 160.0),
                             (200.0, 1500.0, 160.0)]):
    player.location = sdk_stubs.vector(*spot)
    rope.update(player, int((0.6 + step * 0.05) * SECOND))
check("swinging wide around the anchor does not end the pull", rope.holds)
settings.arrival_distance.value = settings.arrival_distance.default_value

# Time. The anchor is put far off so that the pull does not simply arrive first.
player, rope = fresh(hit=(9000.0, "StaticMeshActor"))
settings.longest_pull.value = 0.5
rope.fire(player, 0)
rope.update(player, int(1.8 * SECOND))
fly(player, rope, 1.8, 2.2)
check("the limit counts from the moment the hook sets, not from the press", rope.holds)
fly(player, rope, 2.2, 2.4)
check("a pull longer than the limit ends", not rope.busy)
check("and says why", any("let go: too long" in line for line in state["misc"]))

player, rope = fresh(hit=(9000.0, "StaticMeshActor"))
settings.longest_pull.value = 0.0
rope.fire(player, 0)
rope.update(player, int(1.8 * SECOND))
fly(player, rope, 1.8, 3.5)
check("a limit of zero means no limit at all", rope.holds)
settings.longest_pull.value = 4.0

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
