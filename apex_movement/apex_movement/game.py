"""Finds the player character and the movement assets, and reads the state every movement needs.

The character changes with every level load, so it is looked up again every second rather than kept forever. A level
load can also unload an asset, so the asset is dropped with the character and found again when next needed.
"""

import math
import re
from itertools import islice
from typing import Any

import unrealsdk
from mods_base import get_pc

REFRESH_NS = 1_000_000_000
SLIDE_ASSET = ("OakControlledMove", "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Slide.Move_Slide")
DASH_ASSET = ("OakControlledMove", "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Dash.Move_Dash")
CLIMB_ANIMATION = ("AnimSequence",
                   "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Wall_Climb_U.AS_Wall_Climb_U")
ANIM_INSTANCE = "/Script/Engine.AnimInstance"
ARMS_MESH = "FirstPersonArms"
# Bounded: a level held 202 to 322 animation instances in sessions F and G (2026-09-17).
MAX_ANIM_INSTANCES = 20_000

_character: Any = None
_anim: Any = None
_arms: Any = None
# Keyed by the fixed asset names above only, so it never holds more than those.
_assets: dict[tuple[str, str], Any] = {}
_next_refresh_ns = 0


def refresh(now_ns: int) -> bool:
    """Looks the player up again when due; True when the character changed since the last look."""
    global _character, _anim, _arms, _next_refresh_ns
    if now_ns < _next_refresh_ns:
        return False
    _next_refresh_ns = now_ns + REFRESH_NS
    pc = get_pc(possibly_loading=True)
    found = getattr(pc, "OakCharacter", None) if pc is not None else None
    if found == _character:
        return False
    _character = found
    _arms = None
    _assets.clear()
    _anim = found.Mesh.GetAnimInstance() if found is not None else None
    return True


def character() -> Any:
    return _character


def controller() -> Any:
    """The player controller; None while the game is loading."""
    return get_pc(possibly_loading=True)


def anim() -> Any:
    return _anim


def arms_anim() -> Any:
    """The first-person arms' animation, what the player sees; None while it is not found.

    character.FirstPersonArms is no Python attribute (session E, 2026-09-17): the arms are the animation instance whose
    mesh is named FirstPersonArms, belongs to the character and answers with that instance (session F). Looked up once
    per character, when first needed.
    """
    global _arms
    if _arms is None and _character is not None:
        for instance in islice(unrealsdk.find_all(ANIM_INSTANCE, exact=False), MAX_ANIM_INSTANCES):
            mesh = instance.Outer
            if (mesh is not None and str(mesh.Name) == ARMS_MESH and mesh.Outer == _character
                    and mesh.GetAnimInstance() == instance):
                _arms = instance
                break
    return _arms


def _asset(name: tuple[str, str]) -> Any:
    found = _assets.get(name)
    if found is None:
        try:
            found = unrealsdk.find_object(*name)
        except ValueError:
            # Expected during a level load; looked up again on the next call rather than failing the movement.
            return None
        _assets[name] = found
    return found


def slide_asset() -> Any:
    """Move_Slide, the slide's data shared by every player; None while the game has not loaded it."""
    return _asset(SLIDE_ASSET)


def dash_asset() -> Any:
    """Move_Dash, the dash's data shared by every player; None while the game has not loaded it."""
    return _asset(DASH_ASSET)


def climb_animation() -> Any:
    """AS_Wall_Climb_U, the arms' climb up; None while the game has not loaded it."""
    return _asset(CLIMB_ANIMATION)


def forget() -> None:
    global _character, _anim, _arms, _next_refresh_ns
    _character = _anim = _arms = None
    _assets.clear()
    _next_refresh_ns = 0


def movement_mode(movement: Any) -> str:
    """The movement mode as its short name, such as MOVE_Falling."""
    text = repr(movement.MovementMode)
    found = re.search(r"MOVE_\w+", text)
    return found.group(0) if found else text


def is_on_ground(movement: Any) -> bool:
    return movement_mode(movement) == "MOVE_Walking"


def is_in_air(movement: Any) -> bool:
    return movement_mode(movement) == "MOVE_Falling"


def is_sliding(movement: Any) -> bool:
    move = movement.ControlledMoveReplicationData.ControlledMove
    asset = slide_asset()
    return move is not None and asset is not None and move == asset


def input_mappings() -> list[Any]:
    """The game's key list for the player, empty while no player controller exists."""
    pc = get_pc(possibly_loading=True)
    return list(pc.PlayerInput.EnhancedActionMappings) if pc is not None else []


def is_aiming(character: Any) -> bool:
    zoom = character.ZoomState
    return bool(zoom.bWantsToZoom) or getattr(zoom.State, "name", str(zoom.State)) != "NotZoomed"


def horizontal_speed(movement: Any) -> float:
    velocity = movement.Velocity
    return math.hypot(velocity.X, velocity.Y)


def set_horizontal_speed(movement: Any, speed: float) -> None:
    """Scales the horizontal velocity to a speed, keeping its direction and the vertical velocity."""
    velocity = movement.Velocity
    current = math.hypot(velocity.X, velocity.Y)
    if current < 1.0:
        return
    scale = speed / current
    # Assigned whole, like BL4_SuperDash: the game queues AddImpulse calls and can release them later as a spike.
    movement.Velocity = unrealsdk.make_struct("Vector", X=velocity.X * scale, Y=velocity.Y * scale, Z=velocity.Z)


def stick_direction(character: Any) -> tuple[float, float]:
    """The move input, flat and in world axes; keyboard movement always reads as fully pushed."""
    vector = character.GetLastMovementInputVector()
    return float(vector.X), float(vector.Y)


def stick(character: Any) -> float:
    """How far the move input is pushed, 0 to 1."""
    return math.hypot(*stick_direction(character))


def view_yaw(character: Any) -> float | None:
    """The camera's heading in degrees; None while the character has no controller for a moment (seen 2026-09-17)."""
    controller = character.Controller
    return None if controller is None else float(controller.GetControlRotation().Yaw)


def altitude(character: Any) -> float:
    return float(character.K2_GetActorLocation().Z)


def jump_type(movement: Any) -> str:
    """The kind of jump under way, by its short name, such as SprintJump."""
    return str(movement.CurrentJump.JumpType.TagName).rsplit(".", 1)[-1]


def jump_count(character: Any) -> int:
    return int(character.JumpCurrentCount)


def set_jump_count(character: Any, count: int) -> None:
    character.JumpCurrentCount = count


def half_height(character: Any) -> float:
    """Half the collision capsule's height: 93 standing, read on 2026-09-17."""
    return float(character.CapsuleComponent.GetScaledCapsuleHalfHeight())


def is_mantling(movement: Any) -> bool:
    # ActionIndex goes from -1 to 0 for the whole mantle (verified 2026-09-16, question 2).
    return int(movement.ReplicatedMantleState.ActionIndex) >= 0


def can_mantle(movement: Any) -> bool:
    # True for about 35 ms near the top of a ledge during a climb, when the game would mantle with Croix held (session D).
    return bool(movement.CanStartPassiveMantle())


def is_near_game_climb(movement: Any) -> bool:
    # Filled as the player nears one of the game's own climbing walls (verified 2026-09-17, M4).
    return len(movement.LadderState.OverlappingClimbables) > 0


def in_controlled_move(movement: Any) -> bool:
    """Asked of the game, not read from its network copy: the copy keeps a ground slam after landing until a slide
    replaces it (session 3, 2026-09-18), and every climb in between was refused."""
    return bool(movement.IsPerformingControlledMove())


def controlled_move_name(movement: Any) -> str:
    """The game's current controlled move by name (Move_Slide, Move_GroundSlam...); empty when there is none."""
    move = movement.ControlledMoveReplicationData.ControlledMove
    return "" if move is None else str(getattr(move, "Name", "?"))


def set_velocity(movement: Any, x: float, y: float, z: float) -> None:
    movement.Velocity = unrealsdk.make_struct("Vector", X=x, Y=y, Z=z)
