"""The shot: one ray along the camera, and the rule that tells a grapple from a punch.

The recipe is Apex Movement's, verified in game on 2026-09-16: KismetSystemLibrary.LineTraceSingle
called on the class default object, the character as world context, every output and drawing
parameter passed.

Channel 2, not the visibility channel 0. Measured on 2026-09-17 on six walls: channel 2 met the
panel every time, while channel 0 went straight through three of them. Those panels block the
player, so a grapple that ignored them would send him inside the level.

Why the rule exists at all: in Borderlands the grapple key is also the punch key, and the game
decides between them by whether there is a grapple point in front of you. This mod grapples every
surface, so without a rule of its own it would take the punch away for good (Kevin, 2026-09-20).
"""

import math
import re
from dataclasses import dataclass
from typing import Any

import unrealsdk

from . import game_target, report

TRACE_CHANNEL = 2
# Class names that mean a living thing rather than a surface. Hitting one is a punch.
BEINGS = ("char", "vehicle", "enemy", "bpchar")
# Spawn contains the letters Pawn: OakSpawnPoint was wrongly rejected on 2026-09-21.
# Still match a separate later Pawn, e.g. SpawnedAIPawn; never exempt all names containing Spawn.
PAWN = re.compile(r"(?<!s)pawn")
MAX_CLASS_NAME = 256
MAX_OBJECT_NAME = 256
MAX_REFUSALS = 200
NO_SURFACE = "no surface in range"
TOO_CLOSE = "too close"
NATIVE_GRAPPLE = "native grapple"
LIVING_TARGET = "living target"
NATIVE_MELEE = "native melee interaction"
# These shrine actors are activated with the melee action itself. Their measured class is the
# generic LootableObject, so the instance family is required to avoid protecting every loot box.
NATIVE_MELEE_OBJECTS = ("transhumanistshrine",)
# The game's own grapple points, verified in game on 2026-09-20: the class is exactly GrapplePoint.
# The ray rarely meets it, though — of 24 shots at the game's own pads, 13 met the level cell behind
# it, 9 a static mesh and only 2 the point itself, which is why standing aside on the hit alone
# worked 5 times out of 20 (Kevin). So the point is looked for near the aimed spot instead.
GAME_GRAPPLES = ("grapple",)
GAME_POINT_CLASS = "GrapplePoint"
# How near the aimed spot one of the game's points has to sit to count as the thing aimed at. Its
# pad is a few metres across and the point sits in front of the surface, not on it.
GAME_POINT_REACH = 400.0
# Bounded: a level holds a handful of these, and a runaway list must not freeze a key press.
MAX_POINTS = 500
# The first hit actors are written to the log so that what the game really answers is on record
# rather than guessed. Bounded, and it is the class names that are counted, not the hits.
MAX_NAMED = 20

_library: Any = None
_named: set[str] = set()
_counted = False
_refusals = 0


@dataclass(frozen=True)
class Shot:
    """What one ray met: where, how far, and the name of the thing it met ("" when the game will not say)."""

    anchor: tuple[float, float, float]
    distance: float
    hit_name: str
    hit_object_name: str = ""


def reset() -> None:
    global _library, _counted, _refusals
    _library = None
    _counted = False
    _refusals = 0
    _named.clear()


def _kismet() -> Any:
    global _library
    if _library is None:
        _library = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    return _library


def look(character: Any, start: tuple[float, float, float], facing: tuple[float, float, float],
         reach: float, ignore: list | None = None) -> Shot | None:
    """One ray from `start` along `facing`; None when it met nothing within `reach`."""
    end = tuple(start[axis] + facing[axis] * reach for axis in range(3))
    hit, _ignored, result = _kismet().LineTraceSingle(
        character,
        unrealsdk.make_struct("Vector", X=start[0], Y=start[1], Z=start[2]),
        unrealsdk.make_struct("Vector", X=end[0], Y=end[1], Z=end[2]),
        TRACE_CHANNEL, False, list(ignore or []), 0, unrealsdk.make_struct("HitResult"), True,
        unrealsdk.make_struct("LinearColor"), unrealsdk.make_struct("LinearColor"), 0.0,
    )
    if not hit:
        return None
    distance = float(result.Distance)
    # Worked out from the distance rather than read from the hit's own Location: the distance is the
    # one field this trace is already known to answer (Apex Movement reads it and nothing else).
    anchor = tuple(start[axis] + facing[axis] * distance for axis in range(3))
    hit_name, hit_object_name = _identity_of(result)
    return Shot(anchor=anchor, distance=distance, hit_name=hit_name, hit_object_name=hit_object_name)


def _identity_of(result: Any) -> tuple[str, str]:
    """The class and instance of what was hit, or empty names when this build will not say.

    Three ways in, because which of them a HitResult offers is not established in Borderlands 4.
    """
    for reach in (lambda: result.HitObjectHandle.Actor, lambda: result.Actor,
                  lambda: result.Component.GetOwner()):
        try:
            actor = reach()
        except Exception:
            continue
        if actor is None:
            continue
        class_name = str(getattr(getattr(actor, "Class", None), "Name", ""))[:MAX_CLASS_NAME]
        object_name = str(getattr(actor, "Name", ""))[:MAX_OBJECT_NAME]
        if class_name or object_name:
            _tell_once(class_name or object_name)
            return class_name, object_name
    return "", ""


def _tell_once(name: str) -> None:
    if name in _named or len(_named) >= MAX_NAMED:
        return
    _named.add(name)
    report.note(f"aimed at {name}")


def is_being(hit_name: str) -> bool:
    """True when the name reads as something alive rather than a surface."""
    lowered = hit_name[:MAX_CLASS_NAME].lower()
    return any(word in lowered for word in BEINGS) or PAWN.search(lowered) is not None


def is_game_grapple(hit_name: str) -> bool:
    """True when the name reads as one of the game's own grapple points."""
    lowered = hit_name.lower()
    return any(word in lowered for word in GAME_GRAPPLES)


def is_native_melee(shot: Shot) -> bool:
    """True only for measured object families whose interaction is the melee action itself."""
    if shot.hit_name.lower() != "lootableobject":
        return False
    lowered = shot.hit_object_name[:MAX_OBJECT_NAME].lower()
    return any(marker in lowered for marker in NATIVE_MELEE_OBJECTS)


def game_point_near(anchor: tuple[float, float, float]) -> bool:
    """True when one of the game's own grapple points sits near the aimed spot.

    Asked of the level rather than of the ray, because the ray almost never meets the point itself.
    """
    try:
        points = unrealsdk.find_all(GAME_POINT_CLASS, exact=False)
    except Exception as exc:
        report.error_once("game_points", f"the game's grapple points could not be listed: {exc!r}")
        return False
    found = 0
    for point in points:
        found += 1
        if found > MAX_POINTS:
            break
        if game_target.mine(point):
            # The mod's own point sits exactly on the aimed spot: it is never the game's.
            continue
        try:
            spot = point.K2_GetActorLocation()
            gap = math.dist(anchor, (float(spot.X), float(spot.Y), float(spot.Z)))
        except Exception:
            # A point being destroyed while the level streams; the next press looks again.
            continue
        if gap <= GAME_POINT_REACH:
            return True
    _count_once(found)
    return False


def _count_once(found: int) -> None:
    """Says once how many of the game's points the level holds, so a silent zero is not mistaken for none near."""
    global _counted
    if _counted:
        return
    _counted = True
    report.note(f"the level holds {found} of the game's grapple points")


def refusal(shot: Shot | None, punch_range: float, melee_wins: bool, keep_game_grapple: bool,
            keep_native_melee: bool = True) -> str | None:
    """The single authority for deciding whether this collision belongs to the mod."""
    if shot is None:
        return NO_SURFACE
    if keep_native_melee and is_native_melee(shot):
        return NATIVE_MELEE
    # Nearby known surfaces still grapple; melee keeps nearby beings and unidentified hits.
    if shot.distance < punch_range and (not shot.hit_name or is_being(shot.hit_name)):
        return TOO_CLOSE
    if keep_game_grapple and (is_game_grapple(shot.hit_name) or game_point_near(shot.anchor)):
        return NATIVE_GRAPPLE
    return LIVING_TARGET if melee_wins and is_being(shot.hit_name) else None


def grapples(shot: Shot | None, punch_range: float, melee_wins: bool,
             keep_game_grapple: bool = False, *, keep_native_melee: bool = True,
             explain: bool = False) -> bool:
    """False leaves the key to the game. Only actual presses request bounded refusal logging."""
    global _refusals
    reason = refusal(shot, punch_range, melee_wins, keep_game_grapple, keep_native_melee)
    if reason is not None and explain and _refusals < MAX_REFUSALS:
        _refusals += 1
        label = (shot.hit_object_name or shot.hit_name) if shot else "none"
        name = re.sub(r"[^a-zA-Z0-9_]", "?", label[:MAX_OBJECT_NAME])
        distance = f"{shot.distance:.0f} cm" if shot else "unknown"
        report.note(f"grapple refused: {reason}, hit={name}, distance={distance}")
    return reason is None
