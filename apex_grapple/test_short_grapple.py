"""Close surfaces must produce a real pull rather than an immediate arrival after takeoff."""

import math
import sys

import grapple_fixture as fixture
import sdk_stubs
from apex_grapple import aim, beam, game, settings

failures = []
STEP = 0.016


def check(label, passed):
    print(("OK" if passed else "FAIL") + " | " + label)
    if not passed:
        failures.append(label)


def advance(player, rope, now):
    point = game.location(player)
    speed = game.velocity(player.CharacterMovement)
    player.location = sdk_stubs.vector(*(point[i] + speed[i] * STEP for i in range(3)))
    rope.update(player, now)


for distance in (100, 150, 200, 400, 900, 2000):
    player, rope = fixture.fresh(hit=(float(distance), "StaticMeshActor"))
    hands = sdk_stubs.FakeArms(player)
    hands.Outer.DoesSocketExist = lambda name: True
    hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
    fixture.state["anim_instances"] = [hands]
    settings.show_rope.value = True
    accepted = rope.fire(player, 0)
    check(f"{distance} cm wall is grappled", accepted)
    if not accepted:
        continue
    component = beam._component
    contact = int(distance / settings.hook_speed.value * fixture.SECOND)
    rope.update(player, contact)
    now = contact + int(STEP * fixture.SECOND)
    advance(player, rope, now)
    check(f"{distance} cm survives the first pull frame with hands and rope",
          rope.holds and hands.active_montage is not None and beam._component is component)
    check(f"{distance} cm starts pulling toward the wall", game.velocity(player.CharacterMovement)[0] > 0)
    for _ in range(150):
        if not rope.busy:
            break
        now += int(STEP * fixture.SECOND)
        advance(player, rope, now)
    check(f"{distance} cm covers meaningful distance toward the wall", player.location.X > distance * .25)
    check(f"{distance} cm releases normally", not rope.busy and component in fixture.state["destroyed"])
    if distance == 2000:
        check("the configured arrival distance still governs long shots",
              math.dist(game.location(player), rope.anchor) <= settings.arrival_distance.value)
    rope.reset()

for name in ("StaticMeshActor", "GbxPackedLevelStreamingCell", "OakSpawnPoint", "LandscapeStreamingProxy"):
    shot = aim.Shot(anchor=(100, 0, 160), distance=100, hit_name=name)
    check(f"near surface {name} does not turn into a punch", aim.grapples(shot, 200, True))
for name in ("BPChar_Enemy_Ripper", "OakCharacter", "AIPawn_Basic", ""):
    shot = aim.Shot(anchor=(100, 0, 160), distance=100, hit_name=name)
    check(f"near enemy or unknown target {name!r} still permits melee", not aim.grapples(shot, 200, True))
check("aiming into the sky still permits melee", not aim.grapples(None, 200, True))
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(bool(failures))
