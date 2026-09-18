"""Tests game access: refresh once a second, change detection, slide asset cache, mode, aiming, speed and stick."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


S = 1_000_000_000
first = sdk_stubs.FakeCharacter()
check("no player before loading", not game.refresh(0) and game.character() is None)

sdk_stubs.use_character(state, first)
check("the player is not looked up again before a second", not game.refresh(S // 2))
check("the player is found after a second", game.refresh(S) and game.character() is first and game.anim() is first.anim)
check("the same player is no change", not game.refresh(2 * S))

second = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, second)
check("a new character after a level load is a change", game.refresh(3 * S) and game.character() is second)

game.forget()
check("forget drops the player", game.character() is None and game.anim() is None)
check("forget makes the next look immediate", game.refresh(3 * S + 1) and game.character() is second)

movement = second.CharacterMovement
check("walking is on the ground", game.movement_mode(movement) == "MOVE_Walking" and game.is_on_ground(movement))
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("falling is not on the ground", not game.is_on_ground(movement))
check("falling is in the air", game.is_in_air(movement))
movement.MovementMode = sdk_stubs.Mode("MOVE_Custom")
check("a custom mode, such as a mantle, is neither", not game.is_in_air(movement) and not game.is_on_ground(movement))
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("an unknown mode text is kept", game.movement_mode(types.SimpleNamespace(MovementMode="odd")) == "'odd'")

check("not aiming by default", not game.is_aiming(second))
second.ZoomState.bWantsToZoom = True
check("wanting to zoom counts as aiming", game.is_aiming(second))
second.ZoomState.bWantsToZoom = False
second.ZoomState.State = types.SimpleNamespace(name="Zoomed")
check("being zoomed counts as aiming", game.is_aiming(second))

second.input = sdk_stubs.vector(0.6, 0.8)
check("the stick reads its length", abs(game.stick(second) - 1.0) < 1e-9)

asset = sdk_stubs.slide_asset(state)
finds = state["finds"]
check("the slide asset is found", game.slide_asset() is asset)
game.slide_asset()
check("the slide asset is found once, then kept", state["finds"] == finds + 1)
third = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, third)
game.refresh(10 * S)
game.slide_asset()
check("a character change looks the slide asset up again", state["finds"] == finds + 2)
game.forget()
game.slide_asset()
check("forget drops the slide asset", state["finds"] == finds + 3)
state["objects"].clear()
game.forget()
check("a slide asset the game has not loaded reads as missing", game.slide_asset() is None)
state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)] = asset
check("a missing slide asset is looked up again", game.slide_asset() is asset)

# The slide checks above emptied the object list: the dash asset is put back for its own checks.
dash_asset = sdk_stubs.FakeDashAsset()
state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)] = dash_asset
check("the dash asset is found", game.dash_asset() is dash_asset)
finds = state["finds"]
game.slide_asset()
game.dash_asset()
check("both assets are kept side by side", state["finds"] == finds)
game.forget()
game.dash_asset()
check("forget drops the dash asset too", state["finds"] == finds + 1)
del state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)]
game.forget()
check("a dash asset the game has not loaded reads as missing", game.dash_asset() is None)
state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)] = dash_asset

check("no controlled move is no slide", not game.is_sliding(movement))
movement.ControlledMoveReplicationData.ControlledMove = asset
check("Move_Slide in progress is a slide", game.is_sliding(movement))
movement.ControlledMoveReplicationData.ControlledMove = object()
check("another controlled move is no slide", not game.is_sliding(movement))
movement.ControlledMoveReplicationData.ControlledMove = asset
state["objects"].clear()
game.forget()
check("without the slide asset nothing reads as a slide", not game.is_sliding(movement))
state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)] = asset
movement.ControlledMoveReplicationData.ControlledMove = None

check("the key list comes from the player controller", game.input_mappings() == state["mappings"])
sdk_stubs.use_character(state, None)
check("without a player controller the key list is empty", game.input_mappings() == [])

movement.Velocity = sdk_stubs.vector(300.0, 400.0, -20.0)
check("the horizontal speed ignores the vertical part", game.horizontal_speed(movement) == 500.0)
game.set_horizontal_speed(movement, 1000.0)
check("a new horizontal speed keeps direction and vertical part",
      (movement.Velocity.X, movement.Velocity.Y, movement.Velocity.Z) == (600.0, 800.0, -20.0))
movement.Velocity = sdk_stubs.vector(0.5, 0.0, 10.0)
game.set_horizontal_speed(movement, 1000.0)
check("a standing still velocity has no direction to scale", movement.Velocity.X == 0.5)

second.Controller = None
check("without a controller the camera heading is unknown", game.view_yaw(second) is None)
second.Controller = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=30.0))
check("the camera heading is read in degrees", game.view_yaw(second) == 30.0)
check("the stick direction is read flat", game.stick_direction(second) == (0.6, 0.8))
second.location = sdk_stubs.vector(1.0, 2.0, 345.0)
check("the altitude is the character's centre height", game.altitude(second) == 345.0)
second.JumpCurrentCount = 2
check("the jump count is read", game.jump_count(second) == 2)
check("the half height comes from the collision capsule", game.half_height(second) == 93.0)
check("no mantle by default", not game.is_mantling(movement))
movement.ReplicatedMantleState.ActionIndex = 0
check("a mantle index of 0 or more is a mantle", game.is_mantling(movement))
movement.ReplicatedMantleState.ActionIndex = -1
check("no game climbing wall nearby by default", not game.is_near_game_climb(movement))
movement.LadderState.OverlappingClimbables = [object()]
check("an overlapping climbing wall is near", game.is_near_game_climb(movement))
movement.LadderState.OverlappingClimbables = []
check("no controlled move by default", not game.in_controlled_move(movement))
movement.performing = True
check("a move the game says it performs counts", game.in_controlled_move(movement))
movement.performing = False
movement.ControlledMoveReplicationData.ControlledMove = types.SimpleNamespace(Name="Move_GroundSlam")
check("a ground slam left in the game's copy after landing does not count: the game is asked, not its copy",
      not game.in_controlled_move(movement))
movement.ControlledMoveReplicationData.ControlledMove = None
game.set_velocity(movement, 1.0, 2.0, 3.0)
check("a velocity is written whole", (movement.Velocity.X, movement.Velocity.Y, movement.Velocity.Z) == (1.0, 2.0, 3.0))

game.forget()
check("no arms without a character, and nothing scanned", game.arms_anim() is None and state["anim_scans"] == 0)
owner = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, owner)
game.refresh(20 * S)
sdk_stubs.add_arms(state, sdk_stubs.FakeCharacter())
sdk_stubs.add_arms(state, owner, mesh_name="FirstPersonLegs")
arms = sdk_stubs.add_arms(state, owner)
check("the arms are the instance on this character's FirstPersonArms mesh", game.arms_anim() is arms)
game.arms_anim()
check("looked up once per character", state["anim_scans"] == 1)
arms.Outer.GetAnimInstance = lambda: None
game.forget()
game.refresh(30 * S)
check("an instance its mesh does not answer with is not the arms", game.arms_anim() is None and state["anim_scans"] == 2)
game.arms_anim()
check("missing arms are looked up again", state["anim_scans"] == 3)
arms.Outer.GetAnimInstance = lambda: arms
other = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, other)
game.refresh(40 * S)
check("a character change forgets the arms", game.arms_anim() is None)
climb_up = state["objects"][("AnimSequence", sdk_stubs.CLIMB_ANIMATION_PATH)] = sdk_stubs.FakeSequence(0.6)
check("the climb animation is the game's first-person climb up", game.climb_animation() is climb_up)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
