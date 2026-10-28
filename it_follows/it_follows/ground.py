"""Where It Follows puts an enemy brought back: on the ground straight under a point of the hunter's way, found by a
trace, never at the hunter's own height, never deep under him, never on water.

Why (docs/RUN/enquetes/2026-10-11-horde-sur-la-terre.md): trial 6j put the cats at the hunter's height, and where his
vehicle crossed water four stayed stuck above it or in it for about 40 s; Kevin then (decision 28): never in deep
water. Trial 6k asked the engine's navigation, which the game does not have (no NavigationData at all, its enemies walk
on Gearbox's GbxNav). Kevin chose this trace instead (2026-10-11): KismetSystemLibrary.LineTraceSingle on channel 2,
the recipe Apex Movement (2026-09-16) and BL4 Arena's ground.py verified in game.
Under deep water, the bed lies farther below the hunter's vehicle than DROP_CM: not found. What the trace meets is
said; a meeting named water is refused: the trace does meet water (trials 6l and 6m, vérifié en jeu, the sea as
WaterBodyOcean_...OceanCollisionBoxComponent). So is a meeting on a character or a projectile, which is no part of the
world (decision 72): in trials 6m to 8e, 426 of the 7,579 places found lay on a character and 14 on a projectile, and
the enemy was put there, as a cat 4 m above the hunter on the collision bubble of a flying bat (trial 6r); in trial
15, Kevin saw beasts born at his height beside a bridge, walking on the air.
"""

import math
from typing import Any, Callable

import unrealsdk

from .characters import reads

LIBRARY = "KismetSystemLibrary"
TRACE_CHANNEL = 2
# From this far above the point on the hunter's way, the ground rising behind him.
TRACE_UP_CM = 100.0
# Down to this far below it: on foot he stands about 0.9 m above the ground, in a vehicle 1 to 2.5 m (trial 6j, cats
# put at his height falling that far); under a vehicle on water, the bed of water one walks in already lay about 3.2 m
# below (trial 6j, non vérifié), deep water's farther.
DROP_CM = 250.0
# The enemy's centre goes its half height above the ground met, and this much more, to drop onto it.
CLEARANCE_CM = 20.0
# An enemy whose half height cannot be read: a cat stands 1 to 1.4 m tall (trial 6k).
HALF_HEIGHT_CM = 70.0
LOGGED_CALLS = 3
WATER = "water"
NOT_WORLD = "not_world"
# How the names of the actors that are no part of the world begin, as met in trials 6m to 8e: Char_BatRanged_…,
# Char_CatYoung_…, Proj_PhalanxLootBubbleShield_….
NOT_WORLD_OWNERS = ("Char_", "Proj_")


def _vector(x: float, y: float, z: float) -> Any:
    return unrealsdk.make_struct("Vector", X=x, Y=y, Z=z)


def _met(result: Any, field: str) -> str | None:
    """The full name of what a field of the hit holds, or None when it holds nothing or cannot be read."""
    try:
        target = getattr(result, field)
        return None if target is None else reads.clean(target._path_name())
    except Exception:
        return None


def owner(path: str) -> str:
    """The name of the actor whose component a path names, as …:PersistentLevel.<actor>.<component>; else the
    segment before the component's."""
    parts = path.rsplit(":", 1)[-1].split(".")
    if "PersistentLevel" in parts[:-1]:
        return parts[parts.index("PersistentLevel") + 1]
    return parts[-2] if len(parts) > 1 else ""


class GroundTrace:
    """announce(call, log, **fields) notes a call before it happens, written to the log for the first LOGGED_CALLS
    traces only. Keeps each enemy's half height, read once, until the enemy is forgotten."""

    def __init__(self, announce: Callable[..., None]) -> None:
        self.announce = announce
        self.calls = 0
        self.broken: str | None = None
        # The library's default object, through a weak pointer as every game object It Follows keeps.
        self.library: Any = None
        self.heights: dict[str, float] = {}

    def ground(self, name: str, mover: Any, point: tuple, up_cm: float = TRACE_UP_CM, down_cm: float = DROP_CM
               ) -> tuple[str, tuple | None, str | None]:
        """("found", where the enemy's centre goes, what was met) under point, traced from up_cm above it;
        ("no_ground", None, None) when nothing is met down to down_cm below it; ("water", None, what was met);
        ("not_world", None, what was met) on a character or a projectile; ("call_failed:<error>", None, None) when the
        trace failed, this time or before. Trial 8c: It Follows' camps are laid so, from farther above and below."""
        if self.broken is not None:
            return self.broken, None, None
        self.calls += 1
        self.announce("LineTraceSingle", log=self.calls <= LOGGED_CALLS, on=name)
        x, y, z = point
        try:
            hit, _ignored, result = self._library().LineTraceSingle(
                mover, _vector(x, y, z + up_cm), _vector(x, y, z - down_cm), TRACE_CHANNEL, False, [], 0,
                unrealsdk.make_struct("HitResult"), True, unrealsdk.make_struct("LinearColor"),
                unrealsdk.make_struct("LinearColor"), 0.0)
            met = float(result.ImpactPoint.Z) if hit else math.nan
        except Exception as error:
            self.broken = f"call_failed:{type(error).__name__}"
            return self.broken, None, None
        if not math.isfinite(met):
            return "no_ground", None, None
        what, material = _met(result, "Component"), _met(result, "PhysMaterial")
        if any(WATER in (text or "").lower() for text in (what, material)):
            return WATER, None, what or material
        if what is not None and owner(what).startswith(NOT_WORLD_OWNERS):
            return NOT_WORLD, None, what
        return "found", (x, y, met + self._half_height(name, mover) + CLEARANCE_CM), what

    def forget(self, name: str) -> None:
        """Drops the half height kept for an enemy let go: a run may last an hour or more, its enemies coming and
        going."""
        self.heights.pop(name, None)

    def _library(self) -> Any:
        library = self.library() if self.library is not None else None
        if library is None:
            library = unrealsdk.find_class(LIBRARY).ClassDefaultObject
            self.library = unrealsdk.unreal.WeakPointer(library)
        return library

    def _half_height(self, name: str, mover: Any) -> float:
        if name not in self.heights:
            try:
                height = float(mover.CapsuleComponent.GetScaledCapsuleHalfHeight())
            except Exception:
                height = math.nan
            self.heights[name] = height if math.isfinite(height) and height > 0.0 else HALF_HEIGHT_CM
        return self.heights[name]
