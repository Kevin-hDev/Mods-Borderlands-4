"""Gives the game's own grapple somewhere to go: one grapple point of the mod's, kept under the aim.

Prototype. It answers one question before anything is built on it: does the game grapple to a point
the mod placed, with its own rope?

Why this and not another copy of the rope: the game's grapple draws its rope, plays its hand and
hooks on only to a grapple point. Its settings cannot be changed from here (verified on 2026-09-21:
`NexusConfigStoreGrapple` exposes no field), but it can be started: GrappleAnywhere calls
`ServerStartGrapple()` on the character once its own point is ready (its code; not run by us). This
prototype does not do that yet — it leaves the press to the game's own targeting.

The deferred spawn calls return (actor, transform), per the SDK and the log of 2026-09-21.
Only the actor is passed to the next call. This prototype stays disabled during rope trial A.

The point is placed only where the mod would grapple anyway: on a surface, past punching range, not
on an enemy. Anywhere else it is sent away, so the key still punches (Kevin, 2026-09-20).

Everything is guarded. A point that cannot be placed costs the grapple nothing.
"""

from typing import Any

import unrealsdk
from unrealsdk import unreal

from . import report

POINT_CLASS = "GrapplePoint"
STATICS = "GameplayStatics"
# AlwaysSpawn: a point on a wall overlaps the wall, and any other rule would refuse to place it.
ALWAYS_SPAWN = 1
# Where the point waits when there is nothing to grapple: far below the world, out of every range.
AWAY = (0.0, 0.0, -1_000_000.0)
# Unreal 5 added a scale rule to both halves of a deferred spawn. Verified in game on 2026-09-21:
# "BeginDeferredActorSpawnFromClass() missing 1 required positional argument: 'TransformScaleMethod'".
# MultiplyWithRoot is the engine's own default.
MULTIPLY_WITH_ROOT = 1

_point: Any = None
_broken = False
_placed_once = False
# Whether the point sits on a surface right now, rather than away. A press is handed to the game only
# then: a prototype that fails must leave the player the mod's own grapple, never nothing at all —
# which is what 0.10.0 did on 2026-09-21, when the point could not be placed.
_on_surface = False


def reset() -> None:
    """Forgets the point. The level took it with it; a new one is made at the next aim."""
    global _point, _broken, _placed_once, _on_surface
    _point = None
    _broken = _placed_once = _on_surface = False


def ready() -> bool:
    """True when the game has the mod's point to grapple to, right now."""
    return not _broken and _on_surface and _held() is not None


def mine(actor: Any) -> bool:
    """True for the mod's own point, so the rule that stands aside for the game's points skips it."""
    held = _held()
    return held is not None and actor is held


def follow(character: Any, spot: tuple[float, float, float] | None) -> None:
    """Keeps the point under the aim, or sends it away when there is nothing to grapple."""
    global _on_surface
    if _broken:
        return
    try:
        held = _held()
        if held is None:
            if spot is None:
                return
            held = _spawn(character, spot)
            if held is None:
                return
        _move(held, spot if spot is not None else AWAY)
        _on_surface = spot is not None
    except Exception as exc:
        _fail(exc)


def held_list() -> list:
    """The point, for a ray to pass through: a ray that met it would pull it toward the camera."""
    held = _held()
    return [held] if held is not None else []


def remove() -> None:
    global _point
    held = _held()
    _point = None
    if held is None:
        return
    try:
        held.K2_DestroyActor()
    except Exception as exc:
        report.error_once("target:remove", f"the mod's grapple point would not go away: {exc!r}")


def _held() -> Any:
    return _point() if _point is not None else None


def _spawn(character: Any, spot: tuple[float, float, float]) -> Any:
    global _point, _placed_once
    statics = unrealsdk.find_class(STATICS).ClassDefaultObject
    kind = unrealsdk.find_class(POINT_CLASS)
    where = _transform(spot)
    actor, _ = statics.BeginDeferredActorSpawnFromClass(character, kind, where, ALWAYS_SPAWN, character,
                                                        MULTIPLY_WITH_ROOT)
    if actor is None:
        report.error_once("target:spawn", "the game handed back no grapple point")
        return None
    # Remember the unfinished actor too, so a failed finish can destroy it through the error guard.
    _point = unreal.WeakPointer(actor)
    actor, _ = statics.FinishSpawningActor(actor, where, MULTIPLY_WITH_ROOT)
    if actor is None:
        raise RuntimeError("the game did not finish the grapple point")
    # Held weakly: the level destroys it at a load, and a strong hold would keep a dead actor.
    _point = unreal.WeakPointer(actor)
    if not _placed_once:
        _placed_once = True
        report.note(f"the mod's grapple point is placed: {actor.Name}")
    return actor


def _move(actor: Any, spot: tuple[float, float, float]) -> None:
    actor.K2_SetActorLocation(_vector(spot), False, unrealsdk.make_struct("HitResult"), True)


def _transform(spot: tuple[float, float, float]) -> Any:
    return unrealsdk.make_struct(
        "Transform",
        Rotation=unrealsdk.make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
        Translation=_vector(spot),
        Scale3D=_vector((1.0, 1.0, 1.0)),
    )


def _vector(spot: tuple[float, float, float]) -> Any:
    return unrealsdk.make_struct("Vector", X=spot[0], Y=spot[1], Z=spot[2])


def _fail(exc: Exception) -> None:
    global _broken, _on_surface
    _broken, _on_surface = True, False
    report.error_once("target", f"the mod's grapple point was switched off after an error: {exc!r}")
    remove()
