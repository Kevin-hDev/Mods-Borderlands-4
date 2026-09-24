"""Plays the native wall-climb animation on the third-person body and keeps it facing the wall.

The camera stays free. Facing is written immediately before the body's animation update because the controller can
otherwise turn the actor back between movement frames. Body presentation fails independently from the climb and the
first-person arms: losing this animation must never stop the movement.
"""

import math
from typing import Any

import unrealsdk
from unrealsdk import unreal
from unrealsdk.hooks import Type, add_hook, has_hook, remove_hook

from . import report

SLOT = "FullBody"
BLEND_S = 0.2
HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = f"{__package__}:climb_body"
CHARACTERS = ("DarkSiren", "ExoSoldier", "Gravitar", "Paladin")
SEQUENCE_PATH = "/Game/PlayerCharacters/{character}/Animation/3rd/CharacterSkills/AS_Wall_Climb_U.AS_Wall_Climb_U"

_character_pointer: Any = None
_body_pointer: Any = None
_wall: Any = None
_playing = False
_broken = False
_announced = False


def _body() -> Any:
    return _body_pointer() if _body_pointer is not None else None


def _sequence(body: Any) -> Any:
    """Finds the direct asset whose skeleton belongs to the current character; at most four fixed lookups."""
    skeleton = getattr(body, "CurrentSkeleton", None)
    if skeleton is None:
        return None
    for character in CHARACTERS:
        try:
            sequence = unrealsdk.find_object("AnimSequence", SEQUENCE_PATH.format(character=character))
        except ValueError:
            continue
        if (str(getattr(sequence, "Name", "")) == "AS_Wall_Climb_U"
                and getattr(sequence, "Skeleton", None) == skeleton):
            return sequence
    return None


def _remove_hook() -> None:
    if has_hook(HOOK_PATH, Type.PRE, IDENTIFIER):
        remove_hook(HOOK_PATH, Type.PRE, IDENTIFIER)


def _forget() -> None:
    global _character_pointer, _body_pointer, _wall, _playing
    _character_pointer = _body_pointer = _wall = None
    _playing = False


def start(character: Any, wall: Any, longest_climb_s: float) -> None:
    global _character_pointer, _body_pointer, _wall, _playing, _announced
    if _broken or character is None or wall is None:
        return
    body = character.Mesh.GetAnimInstance()
    sequence = _sequence(body)
    if body is None or sequence is None:
        report.error_once("climb_body:missing", "body climb animation unavailable for the current character")
        return
    played = False
    try:
        loops = math.ceil(longest_climb_s / float(sequence.GetPlayLength())) + 1
        body.PlaySlotAnimationAsDynamicMontage(
            Asset=sequence, SlotNodeName=SLOT, BlendInTime=BLEND_S, BlendOutTime=BLEND_S, InPlayRate=1.0,
            LoopCount=loops, BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=0.0,
        )
        played = True
        _character_pointer = unreal.WeakPointer(character)
        _body_pointer = unreal.WeakPointer(body)
        _wall = wall
        _playing = True
        _remove_hook()
        add_hook(HOOK_PATH, Type.PRE, IDENTIFIER, before_update)
        if not _announced:
            _announced = True
            report.note(f"climb animation playing on the third-person body, {loops} loops at most")
    except Exception as exc:
        if played:
            try:
                body.StopSlotAnimation(BLEND_S, SLOT)
            except Exception:
                pass
        _fail(exc)


def update_wall(wall: Any) -> None:
    global _wall
    if _playing:
        _wall = wall


def before_update(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    if not _playing or obj != _body():
        return
    character = _character_pointer() if _character_pointer is not None else None
    if character is None or _wall is None:
        return
    try:
        current = character.K2_GetActorRotation()
        yaw = math.degrees(math.atan2(float(_wall.into_y), float(_wall.into_x)))
        rotation = unrealsdk.make_struct(
            "Rotator", Pitch=float(current.Pitch), Yaw=yaw, Roll=float(current.Roll))
        character.K2_SetActorRotation(rotation, False)
    except Exception as exc:
        _fail(exc)


def stop() -> None:
    body = _body()
    was_playing = _playing
    _forget()
    try:
        _remove_hook()
        if was_playing and body is not None:
            body.StopSlotAnimation(BLEND_S, SLOT)
    except Exception as exc:
        _fail(exc)


def reset() -> None:
    """Forgets an old character without writing into its destroyed animation instance."""
    global _broken, _announced
    _forget()
    try:
        _remove_hook()
    except Exception as exc:
        report.error_once("climb_body:reset", f"body climb cleanup failed: {exc!r}")
    _broken = _announced = False


def _fail(exc: Exception) -> None:
    global _broken
    _forget()
    try:
        _remove_hook()
    except Exception:
        pass
    _broken = True
    report.error_once("climb_body", f"body climb animation switched off after an error: {exc!r}")
