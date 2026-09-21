"""Finds the player and reads or writes the few things the grapple touches.

The character changes with every level load, so it is looked up again every second rather than kept
forever, and held behind a weak pointer: a key press reaches the mod outside the frame loop, up to
a second after a level change, and must not read a character the game has destroyed.

Everything Apex Movement owns is read here and never written: gravity, air control, the jump
counters. The grapple writes two things only, and both are gone by the next frame anyway — the
velocity, and the movement mode when it takes the player off the ground.
"""

import math
from typing import Any

import unrealsdk
from mods_base import get_pc
from unrealsdk import unreal

from . import hand_anchor, input_list

REFRESH_NS = 1_000_000_000
# Measured on 2026-09-20 over jumps with nothing pressed: 980 exactly, and 1960 under Apex Movement's
# GravityScale of 2. Used only when the game will not say, so that the pull still has a scale to work from.
WORLD_GRAVITY = 980.0
# Where the ray starts when the game gives no camera: the eye is near the top of the capsule, whose half
# height is 93 standing (measured 2026-09-17).
EYE_ABOVE_CENTRE = 60.0

# The game's own grapple assets, named by its own settings (Nexus-Data-Grapple4.ncs, 2026-09-18).
GRAPPLE_ANIMATION = ("AnimSequence",
                     "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Grapple.AS_Grapple")
BEAM_EFFECT = ("NiagaraSystem", "/Game/PlayerCharacters/_Shared/Skills/Effects/Systems/GrappleGrabber/"
                                "NS_Grapple_Beam.NS_Grapple_Beam")

_character_pointer: Any = None
_anim: Any = None
_next_refresh_ns = 0
# Identity of acquired references, independent of which caller observed their transition first.
_context: Any = object()
# Two weak asset references only: Python wrappers do not keep engine objects alive across travel.
_assets: dict[tuple[str, str], Any] = {}


def refresh(now_ns: int, at_once: bool = False) -> bool:
    """Refreshes the complete session; an expired owner or changed animation is a transition."""
    global _character_pointer, _anim, _next_refresh_ns, _context
    previous = character()
    expired = _character_pointer is not None and previous is None
    if now_ns < _next_refresh_ns and not at_once and not expired and _anim is not None:
        return False
    pc = get_pc(possibly_loading=True)
    found = getattr(pc, "OakCharacter", None) if pc is not None else None
    # Commit both references together: failed or late mesh acquisition must remain retryable.
    mesh = getattr(found, "Mesh", None)
    animation = mesh.GetAnimInstance() if mesh is not None else None
    changed = expired or found != previous or animation != _anim
    _character_pointer = unreal.WeakPointer(found) if found is not None else None
    _anim = animation
    _next_refresh_ns = now_ns + REFRESH_NS
    if changed:
        # A menu return may unload both assets without disabling the mod.
        _assets.clear()
        _context = object()
    return changed


def character() -> Any:
    return _character_pointer() if _character_pointer is not None else None


def context() -> Any:
    """The current acquisition identity; session cleanup acknowledges it exactly once."""
    return _context


def anim() -> Any:
    """The animation instance the frame hook belongs to, so the mod runs once per frame and not once per mesh."""
    return _anim


def controller() -> Any:
    return get_pc(possibly_loading=True)


def _asset(name: tuple[str, str]) -> Any:
    pointer = _assets.get(name)
    found = pointer() if pointer is not None else None
    if found is None:
        _assets.pop(name, None)
        try:
            found = unrealsdk.find_object(*name)
        except ValueError:
            # Expected during a level load; looked up again at the next call rather than failing.
            return None
        if found is not None:
            _assets[name] = unreal.WeakPointer(found)
    return found


def grapple_animation() -> Any:
    """AS_Grapple, the game's own grapple animation; None while it has not loaded it."""
    return _asset(GRAPPLE_ANIMATION)


def beam_effect() -> Any:
    """NS_Grapple_Beam, the game's own rope effect; None while it has not loaded it."""
    return _asset(BEAM_EFFECT)


def forget() -> None:
    global _character_pointer, _anim, _next_refresh_ns, _context
    _character_pointer = _anim = None
    _next_refresh_ns = 0
    _context = object()
    _assets.clear()


def input_mappings() -> list[Any]:
    """The game's key list for the player, empty while no player controller exists."""
    pc = get_pc(possibly_loading=True)
    player_input = getattr(pc, "PlayerInput", None)
    mappings = getattr(player_input, "EnhancedActionMappings", ())
    return input_list.snapshot(mappings)


def movement_mode(movement: Any) -> str:
    """The movement mode as its short name, such as MOVE_Falling."""
    text = repr(movement.MovementMode)
    start = text.find("MOVE_")
    if start < 0:
        return text
    end = start
    while end < len(text) and (text[end].isalnum() or text[end] == "_"):
        end += 1
    return text[start:end]


def is_on_ground(movement: Any) -> bool:
    return movement_mode(movement) == "MOVE_Walking"


def location(character: Any) -> tuple[float, float, float]:
    spot = character.K2_GetActorLocation()
    return float(spot.X), float(spot.Y), float(spot.Z)


def velocity(movement: Any) -> tuple[float, float, float]:
    speed = movement.Velocity
    return float(speed.X), float(speed.Y), float(speed.Z)


def set_velocity(movement: Any, speed: tuple[float, float, float]) -> None:
    # Written whole, never pushed: the game queues AddImpulse calls and can release them later as one spike.
    movement.Velocity = unrealsdk.make_struct("Vector", X=speed[0], Y=speed[1], Z=speed[2])


def gravity(movement: Any) -> float:
    """How hard the player falls right now, a positive number. Apex Movement doubles it and the pull follows."""
    try:
        told = abs(float(movement.GetGravityZ()))
    except Exception:
        told = 0.0
    if told > 1.0:
        return told
    return WORLD_GRAVITY * float(movement.GravityScale)


def stick(character: Any) -> tuple[float, float, float]:
    """The move input in world axes, already turned by the camera; a keyboard always reads fully pushed."""
    pushed = character.GetLastMovementInputVector()
    return float(pushed.X), float(pushed.Y), float(pushed.Z)


def aim(character: Any) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    """Where the player looks from and which way: the camera's own spot when the game gives it, the eyes otherwise.

    None while the character has no controller, which happens for a moment at a level change.
    """
    pc = controller()
    manager = getattr(pc, "PlayerCameraManager", None) if pc is not None else None
    if manager is not None:
        try:
            spot, turn = manager.GetCameraLocation(), manager.GetCameraRotation()
            return (float(spot.X), float(spot.Y), float(spot.Z)), _facing(turn)
        except Exception:
            # Falls through to the eyes: an aim that works is worth more than the exact camera spot.
            pass
    own = character.Controller
    if own is None:
        return None
    x, y, z = location(character)
    return (x, y, z + EYE_ABOVE_CENTRE), _facing(own.GetControlRotation())


# The former estimate remains a fallback when the measured socket cannot be read.
HAND_DOWN = 25.0
HAND_RIGHT = 30.0


def hand_spot(character: Any) -> tuple[float, float, float]:
    """The animated grapple socket in world axes, or the previous estimate on read failure."""
    measured = hand_anchor.position(character)
    if measured is not None:
        return measured
    x, y, z = location(character)
    controller = character.Controller
    yaw = math.radians(float(controller.GetControlRotation().Yaw)) if controller is not None else 0.0
    right_x, right_y = -math.sin(yaw), math.cos(yaw)
    return (x + right_x * HAND_RIGHT, y + right_y * HAND_RIGHT, z + EYE_ABOVE_CENTRE - HAND_DOWN)


def pitch_of(facing: tuple[float, float, float]) -> float:
    """How far above the horizon a direction points, in degrees."""
    return math.degrees(math.asin(max(-1.0, min(1.0, facing[2]))))


def _facing(turn: Any) -> tuple[float, float, float]:
    """A rotation as the way it points, in Unreal's axes where a positive pitch looks up."""
    pitch, yaw = math.radians(float(turn.Pitch)), math.radians(float(turn.Yaw))
    return math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)
