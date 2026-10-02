"""The beam on screen: one of the game's own weapon beams, lit between the hand and the spot aimed at.

Verified in game on 2026-10-01 (docs/attaque-rayon/enquetes/2026-10-01-rayon-visuel.md): the game's fire beam
lights outside its weapon by Apex Grapple's rope recipe (put free in the world, unlit, moved to the hand and
turned to the anchor, then lit), and its one parameter, User.Target, takes the spot aimed at in world coordinates.

The game does not keep the effect in memory between two shots (reloaded 37 s apart that day), so it is looked up
at each shot and loaded when missing (game_assets.py).

The beam is only what the player sees: nothing here may stop a hit, and every failure switches the beam off.
"""

import math
from typing import Any, NamedTuple

import unrealsdk
from unrealsdk import unreal

from . import game_assets, report
from .aim import vector

SYSTEM_CLASS = "NiagaraSystem"
TARGET = "User.Target"


class Effect(NamedTuple):
    """One of the game's beam effects and how it is driven, as read in the game's files."""

    path: str
    # Most effects take their far end as a plain vector, some as a position: each has its own setter.
    position: bool = False


_component: Any = None
_effect: Effect | None = None


def _angles(origin: tuple, anchor: tuple) -> tuple[float, float]:
    """Pitch and yaw, in degrees, of the way from the origin to the anchor."""
    east, north, up = (b - a for a, b in zip(origin, anchor))
    return math.degrees(math.atan2(up, math.hypot(east, north))), math.degrees(math.atan2(north, east))


def _rotator(origin: tuple, anchor: tuple) -> Any:
    pitch, yaw = _angles(origin, anchor)
    return unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0)


def _place(component: Any, effect: Effect, hand: tuple, anchor: tuple) -> None:
    component.K2_SetWorldLocationAndRotation(vector(hand), _rotator(hand, anchor), False,
                                             unrealsdk.make_struct("HitResult"), True)
    (component.SetVariablePosition if effect.position else component.SetVariableVec3)(TARGET, vector(anchor))


def light(character: Any, effect: Effect, hand: tuple, anchor: tuple) -> None:
    """Puts the beam in the world and lights it. Silent and harmless when the game will not have it."""
    global _component, _effect
    off()
    try:
        made = unrealsdk.find_class("NiagaraFunctionLibrary").ClassDefaultObject.SpawnSystemAtLocation(
            character, game_assets.load(SYSTEM_CLASS, effect.path), vector(hand), _rotator(hand, anchor),
            unrealsdk.make_struct("Vector", X=1.0, Y=1.0, Z=1.0), False, False, 0, True)
        if isinstance(made, tuple):
            made = made[0] if made else None
        if made is None:
            report.error_once("beam:spawn", "the game handed back no beam")
            return
        _component, _effect = unreal.WeakPointer(made), effect
        _place(made, effect, hand, anchor)
        made.Activate(True)
    except Exception as error:
        report.error_once("beam:light", f"the beam could not be lit: {error!r}")
        off()


def _radius(component: Any) -> int:
    """How far the effect reaches around its middle, as the game draws it: a beam with nothing in it has none."""
    found = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject.GetComponentBounds(
        component, unrealsdk.make_struct("Vector"), unrealsdk.make_struct("Vector"), 0.0)
    return round(float(found[-1] if isinstance(found, tuple) else found))


def state() -> str:
    """What the game says of the lit effect, for the log.

    An effect the game lights without a word can still show nothing: the first white candidate did, its hits
    landing and the log clean (2026-10-01, docs/attaque-rayon/enquetes/2026-10-01-rayon-blanc.md). These two
    readings tell an effect the game has switched off from one that runs unseen. A reading the game refuses is said
    as unread: this is a trace, never a failure of the shot.
    """
    component = _component() if _component is not None else None
    if component is None:
        return "no effect"
    said = []
    for label, read in (("active", lambda: bool(component.IsActive())), ("radius", lambda: _radius(component))):
        try:
            said.append(f"{label} {read()}")
        except Exception as error:
            said.append(f"{label} unread ({type(error).__name__})")
    return "effect " + ", ".join(said)


def follow(hand: tuple, anchor: tuple) -> None:
    """Moves the lit beam's two ends; a beam that refuses is switched off."""
    component = _component() if _component is not None else None
    if component is None:
        return
    try:
        _place(component, _effect, hand, anchor)
    except Exception as error:
        report.error_once("beam:follow", f"the beam stopped following: {error!r}")
        off()


def off() -> None:
    """Hands the beam back to the game, switches it off and removes it; each step tried whatever the others do."""
    global _component
    held, _component = _component, None
    component = held() if held is not None else None
    if component is None:
        return
    for label, action in (("handed back", lambda: setattr(component, "bAutoDestroy", True)),
                          ("switched off", component.Deactivate),
                          ("removed", lambda: component.K2_DestroyComponent(component.GetOwner() or component))):
        try:
            action()
        except Exception as error:
            report.error_once(f"beam:{label}", f"the beam could not be {label}: {error!r}")
