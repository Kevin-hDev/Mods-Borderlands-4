"""The beam on screen: one of the game's own weapon beams, lit between the hand and the spot aimed at.

Verified in game on 2026-10-01 (docs/attaque-rayon/enquetes/2026-10-01-rayon-visuel.md): the game's fire beam
lights outside its weapon by Apex Grapple's rope recipe (put free in the world, unlit, moved to the hand and
turned to the anchor, then lit), and its one parameter, User.Target, takes the spot aimed at in world coordinates.

The game does not keep the effect in memory between two shots (reloaded 37 s apart that day), so it is looked up
at each shot and loaded when missing (game_assets.py).

The beam is only what the player sees: nothing here may stop a hit, and every failure switches the beam off.

The shot's beam is the module's own (light, follow, off, state). The bounce lights a second one between two
enemies (bounce.py): each Beam holds its own effect and says its failures under its own name.
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


def _angles(origin: tuple, anchor: tuple) -> tuple[float, float]:
    """Pitch and yaw, in degrees, of the way from the origin to the anchor."""
    east, north, up = (b - a for a, b in zip(origin, anchor))
    return math.degrees(math.atan2(up, math.hypot(east, north))), math.degrees(math.atan2(north, east))


def _rotator(origin: tuple, anchor: tuple) -> Any:
    pitch, yaw = _angles(origin, anchor)
    return unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=0.0)


def _place(component: Any, effect: Effect, origin: tuple, anchor: tuple) -> None:
    component.K2_SetWorldLocationAndRotation(vector(origin), _rotator(origin, anchor), False,
                                             unrealsdk.make_struct("HitResult"), True)
    (component.SetVariablePosition if effect.position else component.SetVariableVec3)(TARGET, vector(anchor))


def _radius(component: Any) -> int:
    """How far the effect reaches around its middle, as the game draws it: a beam with nothing in it has none."""
    found = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject.GetComponentBounds(
        component, unrealsdk.make_struct("Vector"), unrealsdk.make_struct("Vector"), 0.0)
    return round(float(found[-1] if isinstance(found, tuple) else found))


class Beam:
    """One lit effect between two spots, held weakly. Its name is what its failures are said and counted under."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._component: Any = None
        self._effect: Effect | None = None

    def _lit(self) -> Any:
        return self._component() if self._component is not None else None

    def light(self, character: Any, effect: Effect, origin: tuple, anchor: tuple) -> None:
        """Puts the beam in the world and lights it. Silent and harmless when the game will not have it."""
        self.off()
        try:
            made = unrealsdk.find_class("NiagaraFunctionLibrary").ClassDefaultObject.SpawnSystemAtLocation(
                character, game_assets.load(SYSTEM_CLASS, effect.path), vector(origin), _rotator(origin, anchor),
                unrealsdk.make_struct("Vector", X=1.0, Y=1.0, Z=1.0), False, False, 0, True)
            if isinstance(made, tuple):
                made = made[0] if made else None
            if made is None:
                report.error_once(f"{self.name}:spawn", f"the game handed back no {self.name}")
                return
            self._component, self._effect = unreal.WeakPointer(made), effect
            _place(made, effect, origin, anchor)
            made.Activate(True)
        except Exception as error:
            report.error_once(f"{self.name}:light", f"the {self.name} could not be lit: {error!r}")
            self.off()

    def state(self) -> str:
        """What the game says of the lit effect, for the log.

        An effect the game lights without a word can still show nothing: the first white candidate did, its hits
        landing and the log clean (2026-10-01, docs/attaque-rayon/enquetes/2026-10-01-rayon-blanc.md). These two
        readings tell an effect the game has switched off from one that runs unseen. A reading the game refuses is
        said as unread: this is a trace, never a failure of the shot.
        """
        component = self._lit()
        if component is None:
            return "no effect"
        said = []
        for label, read in (("active", lambda: bool(component.IsActive())), ("radius", lambda: _radius(component))):
            try:
                said.append(f"{label} {read()}")
            except Exception as error:
                said.append(f"{label} unread ({type(error).__name__})")
        return "effect " + ", ".join(said)

    def follow(self, origin: tuple, anchor: tuple) -> None:
        """Moves the lit beam's two ends; a beam that refuses is switched off."""
        component = self._lit()
        if component is None:
            return
        try:
            _place(component, self._effect, origin, anchor)
        except Exception as error:
            report.error_once(f"{self.name}:follow", f"the {self.name} stopped following: {error!r}")
            self.off()

    def off(self) -> None:
        """Hands the beam back to the game, switches it off and removes it; each step tried whatever the others do."""
        component, self._component = self._lit(), None
        if component is None:
            return
        for label, action in (("handed back", lambda: setattr(component, "bAutoDestroy", True)),
                              ("switched off", component.Deactivate),
                              ("removed", lambda: component.K2_DestroyComponent(component.GetOwner() or component))):
            try:
                action()
            except Exception as error:
                report.error_once(f"{self.name}:{label}", f"the {self.name} could not be {label}: {error!r}")


_shot = Beam("beam")
light, follow, off, state = _shot.light, _shot.follow, _shot.off, _shot.state
