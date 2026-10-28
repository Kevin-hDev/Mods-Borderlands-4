"""Jump releases an attached grapple without consuming the jump under default settings."""

import sys

import grapple_fixture as fixture
import sdk_stubs
from apex_grapple import beam, game, keys, session, settings
from unrealsdk.hooks import Block

failures = []


def check(label, passed):
    print(("OK" if passed else "FAIL") + " | " + label)
    if not passed:
        failures.append(label)


def event(key, name):
    return fixture.state["keybinds"][key](sdk_stubs.event(name))


for jump_key in ("SpaceBar", "Gamepad_FaceButton_Bottom", "J"):
    player, rope = fixture.fresh(hit=(2000.0, "StaticMeshActor"))
    mappings = [sdk_stubs.mapping("Action_Grapple", "V"),
                sdk_stubs.mapping("Action_Jump_HoldToGlide", jump_key)]
    keys.bind(mappings, rope)
    session.refresh(0, rope, at_once=True)
    hands = sdk_stubs.FakeArms(player)
    hands.Outer.DoesSocketExist = lambda name: True
    hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
    fixture.state["anim_instances"] = [hands]
    settings.show_rope.value = True
    settings.block_jump.value = True
    player.JumpCurrentCount = 1
    player.JumpMaxCount = 3
    rope.fire(player, 0)
    rope.update(player, int(.4 * fixture.SECOND))
    component = beam._component
    speed = game.velocity(player.CharacterMovement)
    check(f"{jump_key}: attached before jump", rope.holds and component is not None)
    check(f"{jump_key}: release press is consumed", event(jump_key, "IE_Pressed") is Block)
    check(f"{jump_key}: jump detaches the rope", not rope.busy)
    check(f"{jump_key}: visual cleanup follows detachment",
          component in fixture.state["destroyed"] and hands.active_montage is None)
    check(f"{jump_key}: momentum and jump counts are preserved",
          game.velocity(player.CharacterMovement) == speed
          and (player.JumpCurrentCount, player.JumpMaxCount) == (1, 3))
    check(f"{jump_key}: holding does not leak a repeat", event(jump_key, "IE_Repeat") is Block)
    check(f"{jump_key}: matching release stays consumed", event(jump_key, "IE_Released") is Block)
    check(f"{jump_key}: next press is a normal jump", event(jump_key, "IE_Pressed") is None)
    event(jump_key, "IE_Released")
    rope.reset()
    keys.unbind()

player, rope = fixture.fresh(hit=(2000.0, "StaticMeshActor"))
keys.bind(fixture.state["mappings"], rope)
session.refresh(0, rope, at_once=True)
settings.show_rope.value = False
rope.fire(player, 0)
check("during hook flight the normal jump stays available", event("SpaceBar", "IE_Pressed") is None)
check("a jump before attachment does not cancel the shot", rope.busy and not rope.holds)
event("SpaceBar", "IE_Released")
rope.update(player, int(.4 * fixture.SECOND))
settings.block_jump.value = False
check("option off still passes the jump to the game", event("SpaceBar", "IE_Pressed") is None)
check("option off still releases the grapple", not rope.busy)
check("option off does not swallow the release", event("SpaceBar", "IE_Released") is None)
settings.block_jump.value = True
keys.unbind()
check("no jump callback errors", not fixture.state["errors"])
print(f"RESULTAT: {len(failures)} failures")
sys.exit(bool(failures))
