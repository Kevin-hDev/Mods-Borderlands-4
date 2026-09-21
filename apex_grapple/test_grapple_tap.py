"""A tap must not become a release command merely because the wall is close."""

import sys

import grapple_fixture as fixture
import sdk_stubs
from apex_grapple import beam, game, settings

failures = []
SECOND = fixture.SECOND
STEP = 0.016


def check(label, passed):
    print(("OK" if passed else "FAIL") + " | " + label)
    if not passed:
        failures.append(label)


for distance in (50, 75, 101, 150, 203, 256, 441, 2000):
    player, rope = fixture.fresh(hit=(float(distance), "GbxPackedLevelStreamingCell"))
    hands = sdk_stubs.FakeArms(player)
    hands.Outer.DoesSocketExist = lambda name: True
    hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
    fixture.state["anim_instances"] = [hands]
    settings.show_rope.value = True
    settings.keep_game_grapple.value = True
    settings.release_on_key_up.value = True
    start = 10 * SECOND
    rope.fire(player, start)
    component = beam._component
    contact = start + int(distance / settings.hook_speed.value * SECOND)
    lifted = start + int(.11 * SECOND)
    if contact <= lifted:
        rope.update(player, contact)
    rope.key_up(lifted)
    check(f"{distance} cm: a 110 ms tap keeps the shot alive", rope.busy and not rope.key_down)
    if contact > lifted:
        rope.update(player, contact)
    check(f"{distance} cm: tap preserves hands and rope",
          hands.active_montage is not None and beam._component is component)
    now = max(contact, lifted)
    for _ in range(180):
        if not rope.busy:
            break
        now += int(STEP * SECOND)
        point = game.location(player)
        speed = game.velocity(player.CharacterMovement)
        player.location = sdk_stubs.vector(*(point[i] + speed[i] * STEP for i in range(3)))
        rope.update(player, now)
    check(f"{distance} cm: tap pulls toward the wall", player.location.X > distance * .25)
    check(f"{distance} cm: finishes and cleans up", not rope.busy and component in fixture.state["destroyed"])

# Holding still permits an immediate deliberate release; cancellation has no tap delay.
player, rope = fixture.fresh(hit=(150.0, "StaticMeshActor"))
rope.fire(player, 0)
rope.update(player, int(.03 * SECOND))
rope.key_up(int(.25 * SECOND))
check("a held key releases the attached rope", not rope.busy)
rope.fire(player, SECOND)
rope.fire(player, SECOND + int(.05 * SECOND))
check("a second press cancels immediately", not rope.busy)

settings.release_on_key_up.value = False
rope.fire(player, 2 * SECOND)
rope.update(player, 2 * SECOND + int(.03 * SECOND))
rope.key_up(3 * SECOND)
check("the disabled hold option still ignores key release", rope.holds)
rope.reset()
settings.release_on_key_up.value = True
rope.fire(player, 4 * SECOND)
rope.update(player, 4 * SECOND + int(.03 * SECOND))
rope.key_up(4 * SECOND + int(.11 * SECOND))
check("a new shot after reset gets its own press duration", rope.holds)
rope.reset()

print(f"RESULTAT: {len(failures)} failures")
sys.exit(bool(failures))
