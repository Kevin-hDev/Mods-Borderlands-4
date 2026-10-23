"""Reading the game: where an actor stands, how far apart two places are, whether a character is dead, its name, its
path, its definition, a combat zone's radius, the engine's count of images, the objects of a class and how long a
search of them takes. Nothing here writes to the game or calls a function that changes it.

Taken from the trials' census (docs/RUN/sondes/run_census.py) and the two reads of the enemy research it loaded
(mods/perso/apex_probe: actor_definition.py and the radius of apex_territory_radius_patch.py), read on every enemy of
the trials since 6a: It Follows keeps its own copy (decision 45). Each read answers None, or raises ValueError for the
radius, rather than let an error of the game through.
"""

from itertools import islice
import math
import re
import time
from typing import Any, Callable, Iterable, Iterator

import unrealsdk

MAX_TEXT = 200
# The engine's library whose GetFrameCount gives GFrameCounter, the images drawn since the game started (decision
# 102); its default object held weakly, as target.py holds its own.
FRAMES_LIBRARY = "KismetSystemLibrary"
STATICS = "GameplayStatics"
_held: dict[str, Any] = {"frames": None}
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


def frame_count() -> int | None:
    """The images the engine has drawn since the game started, None when it cannot be read."""
    try:
        pointer = _held["frames"]
        library = pointer() if pointer is not None else None
        if library is None:
            library = unrealsdk.find_class(FRAMES_LIBRARY).ClassDefaultObject
            _held["frames"] = unrealsdk.unreal.WeakPointer(library)
        return int(library.GetFrameCount())
    except Exception:
        return None


def search(class_name: str, world: Any = None) -> tuple[Iterable[Any], str]:
    """The objects of a class and its subclasses, and which way they were found. Given an actor of the world in play,
    its actors, with GameplayStatics.GetAllActorsOfClass: 0.03 to 0.06 ms in trial 38, where find_all took 9 to 13 ms
    to go through every object the game holds. find_all also gives the class defaults and the bodies the game keeps
    in its reserve, out of the world (docs/RUN/enquetes/2026-10-16-essai-38-recherches-comparees.md). Without an
    actor, or when the call fails, find_all, said with the error's name."""
    if world is not None:
        try:
            statics = unrealsdk.find_class(STATICS).ClassDefaultObject
            _void, actors = statics.GetAllActorsOfClass(WorldContextObject=world,
                                                        ActorClass=unrealsdk.find_class(class_name), OutActors=[])
            return actors, "actors"
        except Exception as error:
            return unrealsdk.find_all(class_name, exact=False), f"find_all:{type(error).__name__}"
    return unrealsdk.find_all(class_name, exact=False), "find_all"


def timed(find: Callable[[], Iterable[Any]], spent: list[float]) -> Iterator[Any]:
    """What find gives, as it comes, the seconds spent in find and in waiting for each object added to spent[0].
    Trial 37 timed the objects only, and read 0.0 ms at each of 127 censuses: the SDK's find_all does its search when
    called."""
    began = time.perf_counter()
    found = iter(find())
    spent[0] += time.perf_counter() - began
    while True:
        began = time.perf_counter()
        try:
            item = next(found)
        except StopIteration:
            spent[0] += time.perf_counter() - began
            return
        spent[0] += time.perf_counter() - began
        yield item


def zone_radius_cm(zone: Any) -> float:
    """A combat zone's radius in cm (settings.CombatTerritory.Radius); ValueError when unreadable or not finite."""
    try:
        value = float(zone.settings.CombatTerritory.Radius)
    except Exception as error:
        raise ValueError("combat radius unavailable") from error
    if not math.isfinite(value):
        raise ValueError("non-finite combat radius")
    return value
