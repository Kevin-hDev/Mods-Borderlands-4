"""Reading the game: where an actor stands, how far apart two places are, whether a character is dead, its name, its
path, its definition, a combat zone's radius. Nothing here writes to the game or calls a function that changes it.

Taken from the trials' census (docs/RUN/sondes/run_census.py) and the two reads of the enemy research it loaded
(mods/perso/apex_probe: actor_definition.py and the radius of apex_territory_radius_patch.py), read on every enemy of
the trials since 6a: It Follows keeps its own copy (decision 45). Each read answers None, or raises ValueError for the
radius, rather than let an error of the game through.
"""

from itertools import islice
import math
import re
from typing import Any

MAX_TEXT = 200
# Farther than this in one sample (a second) is neither a run nor a drive but a jump, a death or a fast travel: the
# hunter drove 21 m/s at most in trial 6z bis, and his place read 16.8 km away at his death (docs/RUN/sondes/
# run_wave.py).
JUMP_M = 200.0
# GbxActorDef is among the first fields of GbxActorData: the enemy research read no further.
MAX_ACTOR_DATA_PROPERTIES = 8


def clean(value: Any) -> str:
    return str(value).replace("\r", "").replace("\n", "")[:MAX_TEXT]


def path_of(target: Any) -> str:
    try:
        return clean(target._path_name())
    except Exception as error:
        return f"? ({type(error).__name__})"


def camp_of(zone: Any) -> str | None:
    """The name of the camp owning a zone (its Outer, the spawner), None without one."""
    try:
        return clean(zone.Outer.Name) if zone is not None else None
    except Exception:
        return None


def point(target: Any, getter: str = "K2_GetActorLocation") -> tuple[float, float, float] | None:
    """Where the actor stands, in cm; a zone is read with K2_GetComponentLocation."""
    try:
        where = getattr(target, getter)()
        values = (float(where.X), float(where.Y), float(where.Z))
    except Exception:
        return None
    return values if all(math.isfinite(value) for value in values) else None


def metres(a: tuple | None, b: tuple | None) -> float | None:
    if a is None or b is None:
        return None
    return round(math.dist(a, b) / 100.0, 1)


def spot(at: tuple | None) -> list[float] | None:
    """A place in metres to 0.1 m, for the log."""
    return None if at is None else [round(value / 100.0, 1) for value in at]


def dead(actor: Any) -> bool | None:
    """Whether the game counts the character dead, None when it does not say. The game reuses a dead enemy's body for
    the next one (docs/spawn-boss/enquetes/2026-10-05-plusieurs-ennemis.md): a dead one is never called on."""
    try:
        value = actor.HealthState.bCurrentlyDead
    except Exception:
        return None
    return value if type(value) is bool else None


def mode(actor: Any) -> str | None:
    """The character's movement mode, its short name such as MOVE_Swimming or MOVE_None for a rider, read as Apex
    Movement reads it (docs/RUN/sondes/run_trial_kit.py); None when it cannot be read."""
    try:
        text = repr(actor.CharacterMovement.MovementMode)
    except Exception:
        return None
    found = re.search(r"MOVE_\w+", text)
    return found.group(0) if found else None


def definition(actor: Any) -> str | None:
    """The name of the character's definition (GbxActorData.GbxActorDef), None when it cannot be read. Default
    objects are never inspected: only the actor's own data."""
    try:
        data = actor.GbxActorData
        properties = data._type._properties()
    except Exception:
        return None
    for prop in islice(properties, MAX_ACTOR_DATA_PROPERTIES):
        if str(prop.Name) != "GbxActorDef":
            continue
        try:
            name = clean(data._get_field(prop)._name)
        except Exception:
            return None
        return name or None
    return None


def zone_radius_cm(zone: Any) -> float:
    """A combat zone's radius in cm (settings.CombatTerritory.Radius); ValueError when unreadable or not finite."""
    try:
        value = float(zone.settings.CombatTerritory.Radius)
    except Exception as error:
        raise ValueError("combat radius unavailable") from error
    if not math.isfinite(value):
        raise ValueError("non-finite combat radius")
    return value
