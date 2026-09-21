"""Finds the player character and the movement assets, and reads the state every movement needs.

The character changes with every level load, so it is looked up again every second rather than kept forever. A level
load can also unload an asset, so the asset is dropped with the character and found again when next needed.
"""

import math
import re
from typing import Any

import unrealsdk
from mods_base import get_pc
from unrealsdk import unreal

from . import arms, dash_lookup

REFRESH_NS = 1_000_000_000
SLIDE_ASSET = ("OakControlledMove", "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Slide.Move_Slide")
DASH_ASSET = ("OakControlledMove", "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Dash.Move_Dash")
CLIMB_ANIMATION = ("AnimSequence",
                   "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Wall_Climb_U.AS_Wall_Climb_U")
# What refresh found changed. A new character clears what the movements wrote on the old one; a new animation on the
# same character clears nothing, since the character still carries every value written on it. AWAY is the player
# leaving their character for a vehicle, and coming back to that same character: nothing was lost, so nothing is
# forgotten. Treating that as a new character left a gravity of 2 in the game for good (Kevin, 2026-09-20).
CHARACTER = "character"
ANIMATION = "animation"
AWAY = "away"

_character: Any = None
# What character() gives: none as soon as the game destroys the character. Key presses reach the mod outside the frame
# loop, up to REFRESH_NS after a level change, and must not read a destroyed character (review, 2026-09-19).
_character_pointer: Any = None
# The last character found, kept while the player rides a vehicle so that what was written on it can still be put
# back; it answers None once the game has destroyed it, and only then are its values forgotten.
_last_pointer: Any = None
_anim: Any = None
# Keyed by the fixed asset names above only, so it never holds more than those.
_assets: dict[tuple[str, str], Any] = {}

_next_refresh_ns = 0


def refresh(now_ns: int, at_once: bool = False) -> str:
    """Looks the player up again when due, or at once; says what changed since the last look, CHARACTER, ANIMATION
    or ""."""
    global _character, _character_pointer, _last_pointer, _anim, _next_refresh_ns
    if now_ns < _next_refresh_ns and not at_once:
        return ""
    _next_refresh_ns = now_ns + REFRESH_NS
    pc = get_pc(possibly_loading=True)
    found = getattr(pc, "OakCharacter", None) if pc is not None else None
    anim = found.Mesh.GetAnimInstance() if found is not None else None
    if found == _character:
        if anim == _anim:
            return ""
        # Followed on the same character too: an animation kept from before is suspected of leaving the mod silent
        # until it was switched off and on (session 6, 2026-09-18).
        _anim = anim
        arms.forget()
        return ANIMATION
    replaced = found is not None and found != last_character()
    _character, _anim = found, anim
    _character_pointer = unreal.WeakPointer(found) if found is not None else None
    if found is not None:
        _last_pointer = _character_pointer
    arms.forget()
    _assets.clear()
    if replaced:
        dash_lookup.forget()
    return CHARACTER if replaced else AWAY


def character() -> Any:
    return _character_pointer() if _character_pointer is not None else None


def last_character() -> Any:
    """The character the mod last wrote on, even while the player rides a vehicle; None once the game destroyed it."""
    return _last_pointer() if _last_pointer is not None else None


def controller() -> Any:
    """The player controller; None while the game is loading."""
    return get_pc(possibly_loading=True)


def anim() -> Any:
    return _anim


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


def dash_asset(now_ns: int | None = None) -> Any:
    """The dash of the character being played: the one dash_lookup knows, else Move_Dash, which the first four
    characters share. None while the game has loaded neither."""
    found = dash_lookup.current(now_ns)
    return found if found is not None else _asset(DASH_ASSET)


def climb_animation() -> Any:
    """AS_Wall_Climb_U, the arms' climb up; None while the game has not loaded it."""
    return _asset(CLIMB_ANIMATION)


def forget() -> None:
    global _character, _character_pointer, _last_pointer, _anim, _next_refresh_ns
    _character = _character_pointer = _last_pointer = _anim = None
    dash_lookup.forget()
    arms.forget()
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
