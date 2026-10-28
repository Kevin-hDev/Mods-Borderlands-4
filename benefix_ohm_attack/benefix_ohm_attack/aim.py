"""Where the player aims: one ray along the camera, the spot it meets and who stands there.

The ray is Apex Grapple's (verified in game, 2026-09-16): KismetSystemLibrary.LineTraceSingle on the class
default object, the character as world context, every output and drawing parameter passed, channel 2 because it
meets what blocks the player. Trials of 2026-10-01 showed it hands back the enemy under the crosshair.

A thin ray misses an enemy a hair beside the crosshair: the catch (catch.py) looks beside the aim for one.
"""

import math
import re
from dataclasses import dataclass
from typing import Any

import unrealsdk

TRACE_CHANNEL = 2
# Every character shares one class; the species is the object's name without its instance number.
CHARACTERS = "Char_"
ALLIES = ("Char_NPC_",)
INSTANCE_NUMBER = re.compile(r"_\d+$")
MAX_NAME = 80


@dataclass(frozen=True)
class Aim:
    """One frame's aim: where the beam ends, and the enemy it ends on when there is one, with how far it stands.

    For the shot's line of the log (shot_report.py): whether the enemy was caught beside the aim rather than met
    under it, and whether a foe near the aim was left because something hid him."""

    anchor: tuple[float, float, float]
    hit: Any = None
    enemy: Any = None
    species: str = ""
    distance: float = 0.0
    caught: bool = False
    hidden: bool = False


def facing(turn: Any) -> tuple[float, float, float]:
    """A rotation as the way it points, in Unreal's axes where a positive pitch looks up."""
    pitch, yaw = math.radians(float(turn.Pitch)), math.radians(float(turn.Yaw))
    return math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)


def hit_actor(result: Any) -> Any:
    """The actor a ray met. Three ways in: which of them a HitResult offers is not established in this game."""
    for way in (lambda: result.HitObjectHandle.Actor, lambda: result.Actor, lambda: result.Component.GetOwner()):
        try:
            actor = way()
        except Exception:
            continue
        if actor is not None:
            return actor
    return None


def species_of(actor: Any) -> str:
    return INSTANCE_NUMBER.sub("", str(actor.Name)[:MAX_NAME])


def is_enemy(species: str) -> bool:
    """A character that is not an ally by name. Friend and foe are not told apart further: the game's own damage
    data decides who can be hurt."""
    return species.startswith(CHARACTERS) and not species.startswith(ALLIES)


def vector(spot: tuple[float, float, float]) -> Any:
    return unrealsdk.make_struct("Vector", X=spot[0], Y=spot[1], Z=spot[2])


def eye(pc: Any) -> tuple[tuple[float, float, float], Any]:
    """Where the player's camera is, and its rotation."""
    manager = pc.PlayerCameraManager
    spot = manager.GetCameraLocation()
    return (float(spot.X), float(spot.Y), float(spot.Z)), manager.GetCameraRotation()


def ray(character: Any, start: tuple, end: tuple) -> tuple[bool, Any]:
    """A thin ray between two spots: whether it met something, and the game's answer."""
    met, _ignored, result = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject.LineTraceSingle(
        character, vector(start), vector(end), TRACE_CHANNEL, False, [], 0, unrealsdk.make_struct("HitResult"), True,
        unrealsdk.make_struct("LinearColor"), unrealsdk.make_struct("LinearColor"), 0.0)
    return bool(met), result


def touched(result: Any, fallback: tuple) -> tuple[float, float, float]:
    """Where a ray touched what it met; the spot given when the game does not say."""
    try:
        point = result.ImpactPoint
        found = (float(point.X), float(point.Y), float(point.Z))
    except Exception:
        return fallback
    return found if all(math.isfinite(value) for value in found) else fallback


def _met(character: Any, result: Any) -> tuple[Any, str]:
    """(the enemy a ray met, its species): nobody when it met a wall, an ally or the player himself."""
    actor = hit_actor(result)
    if actor is None or actor is character:
        return None, ""
    species = species_of(actor)
    return (actor if is_enemy(species) else None), species


def look(pc: Any, character: Any, reach: float) -> Aim:
    start, turn = eye(pc)
    way = facing(turn)
    end = tuple(start[axis] + way[axis] * reach for axis in range(3))
    met, result = ray(character, start, end)
    if not met:
        return Aim(anchor=end)
    distance = float(result.Distance)
    anchor = tuple(start[axis] + way[axis] * distance for axis in range(3))
    enemy, species = _met(character, result)
    return Aim(anchor=anchor, hit=result, enemy=enemy, species=species, distance=distance if species else 0.0)
