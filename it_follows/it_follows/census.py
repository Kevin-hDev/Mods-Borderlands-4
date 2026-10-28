"""The census: the enemies around the hunter that It Follows may draw into its horde, read among the characters the
game holds, with how many it passed over and why, and who it saw alive and dead. Read only: nothing in the game is
written or called to change.

Kept: every living enemy of every team and kind, flyers and enemies without a zone standing in the world among them
(decision 35: Kevin wants every kind around drawn, and trial 6q passed over bats, drones and some twenty enemies
without a zone). Passed over (docs/RUN/enquetes/2026-10-10-recensement.md): the dead and those the game does not say
alive, bosses (decision 4: one taken from its arena may block a mission), NPCs and companions, characters the game
keeps in its reserve (no zone, far away) and enemies of a world event. The normal mode asks for the bosses too
(decision 90: they get its health and speed, never its chase), kept without their zone, whatever stands around them.
It asks too who killed each enemy and boss read dead (killers.py), for the Hardcore's count.
How many were passed over, and of which kind, is counted (trial 6p): trial 6o drew only cats where Kevin expected other
kinds too. What a character is comes from It
Follows' own table (kinds.py), where the trials read the enemy research's catalogue (decision 45).
"""

from dataclasses import dataclass
from itertools import islice
import math
import time
from typing import Any, Iterable

from . import killers, kinds
from .characters import reads
from .seen import Seen

# The game waits while the census reads (trial 1, docs/RUN/sondes/run_census.py): it stops at MAX_SCAN characters or
# after MAX_SECONDS.
MAX_SCAN = 1000
MAX_SECONDS = 3.0
CHARACTER_CLASS = "OakCharacter"
# A world event's zone lies in a folder of this name (docs/RUN/enquetes/2026-10-10-recensement.md).
WORLD_EVENT = "/Events/"
# Enough reasons, each with its kind, to name what stands around a camp; few enough to keep a log line short.
MAX_SKIPPED_KINDS = 24
MAX_KIND_TEXT = 60
# The game's reserve lies about 3.8 km from the hunter (docs/RUN/enquetes/2026-10-10-recensement.md); an enemy without a
# zone nearer than this stands in the world.
NO_ZONE_NEAR_M = 1000.0


@dataclass(frozen=True)
class Sighting:
    """Who one census saw, by name: the enemies it kept, all alive, and every character it read dead. A name seen
    alive at one census and dead at a later one is a kill, even of an enemy killed before it joined the horde
    (decision 49). kept: the name, kind, zone path and place of each enemy kept, for the kinds of the place
    (zone_kinds.py)."""

    alive: frozenset[str]
    dead: frozenset[str]
    kept: tuple[tuple[str, str, str, tuple | None], ...] = ()
    # When asked: each enemy and boss read dead, by name, with what killers.killed_by says of it.
    killed: tuple[tuple[str, tuple[str, str]], ...] = ()
    # Among them, those another character killed: by name, the killer's name (killers.killer_name).
    killed_by_other: tuple[tuple[str, str], ...] = ()


def _kept(actor: Any, name: str, here: tuple | None, state: bool | None, bosses: bool = False) -> Seen | str:
    """The enemy as read, or why it is not kept: the reason, then its kind once read. state is reads.dead(actor), read
    once by seen_around: a character not said alive is asked nothing more (reads.dead says why). The kind is checked
    before the zone; one without a zone has an empty zone path. A boss is kept only when bosses is asked."""
    if state is not False:
        return "dead_or_unknown"
    definition = reads.definition(actor)
    if definition is None:
        return "unknown_kind:?"
    text = definition[:MAX_KIND_TEXT]
    sort = kinds.kind(definition)
    if sort is None:
        return f"unknown_kind:{text}"
    what, walks = sort
    if what == kinds.OTHER:
        return f"not_enemy:{text}"
    if what == kinds.BOSS:
        if not bosses:
            return f"boss:{text}"
        return Seen(actor, name, definition, None, "", None, 0.0, reads.point(actor), walks, boss=True)
    try:
        zone = actor.GetTerritory()
    except Exception:
        return f"zone_unreadable:{text}"
    if zone is None:
        at = reads.point(actor)
        near = reads.metres(at, here)
        if near is None or near > NO_ZONE_NEAR_M:
            return f"in_reserve:{text}"
        return Seen(actor, name, definition, None, "", None, 0.0, at, walks)
    path = reads.path_of(zone)
    if WORLD_EVENT in path:
        return f"world_event:{text}"
    try:
        radius_m = reads.zone_radius_cm(zone) / 100.0
    except ValueError:
        return f"radius_unreadable:{text}"
    return Seen(actor, name, definition, zone, path, reads.point(zone, "K2_GetComponentLocation"), radius_m,
                reads.point(actor), walks)


def _fighter(actor: Any) -> bool:
    """Whether a dead character was an enemy or a boss, by its definition, a field read as for the living."""
    sort = kinds.kind(reads.definition(actor))
    return sort is not None and sort[0] in (kinds.ENEMY, kinds.BOSS)


def _tally(skipped: dict, why: str) -> None:
    """Counts why a character was passed over, at most MAX_SKIPPED_KINDS reasons, any later one as other."""
    key = why if why in skipped or len(skipped) < MAX_SKIPPED_KINDS else "other"
    skipped[key] = skipped.get(key, 0) + 1


def seen_around(player: Any, seconds: float | None = None, bosses: bool = False, kills: bool = False,
                pc: Any = None, known: frozenset[str] | set[str] = frozenset(),
                in_world: bool = False) -> tuple[list[Seen], dict, Sighting]:
    """Every character read, within seconds (MAX_SECONDS by default): the enemies kept, the bosses among them when
    asked, the reading's counts, and who was seen alive and dead; with kills, who killed each enemy read dead (pc: the
    player's controller). The player and the class defaults count as read, and are neither kept nor tallied. A name
    known (the horde's own) read alive is seen alive and read no further: its kind, zone and place are not asked,
    some 27 µs each, about 3 ms of each census with a full horde (trials 16 to 19); it is never kept, the zone it holds
    being the mod's, which the kinds of the place pass over (zone_kinds.py). in_world: only the characters in the
    world, some 10 ms sooner (reads.search), as the Horde asks; the normal mode reads them all, its Hardcore counting
    its kills on the bodies, which the game soon puts in its reserve, out of the world (decision 105)."""
    deadline = time.monotonic() + (MAX_SECONDS if seconds is None else seconds)
    found: list[Seen] = []
    alive_known: list[str] = []
    dead: set[str] = set()
    killed: list[tuple[str, tuple[str, str]]] = []
    by_other: list[tuple[str, str]] = []
    stats = {"read": 0, "stopped": "complete", "skipped": {}}
    here = reads.point(player)
    # The search alone, apart from the reads of each character (audit of 16 October 2026, A2).
    scan, way = [0.0], ["find_all"]

    def find() -> Iterable[Any]:
        objects, way[0] = reads.search(CHARACTER_CLASS, player if in_world else None)
        return objects

    found_all = reads.timed(find, scan)
    for number, actor in enumerate(islice(found_all, MAX_SCAN + 1)):
        if number >= MAX_SCAN:
            stats["stopped"] = "scan_limit"
            break
        if time.monotonic() > deadline:
            stats["stopped"] = "time_limit"
            break
        stats["read"] += 1
        name = reads.clean(getattr(actor, "Name", "?"))
        if actor == player or name.startswith("Default__"):
            continue
        state = reads.dead(actor)
        if state is True:
            dead.add(name)
            if kills and _fighter(actor):
                killed.append((name, killers.killed_by(actor, player, pc)))
                if killed[-1][1][0].startswith("other:"):
                    by_other.append((name, killers.killer_name(actor)))
        if state is False and name in known:
            alive_known.append(name)
            continue
        seen = _kept(actor, name, here, state, bosses)
        if isinstance(seen, Seen):
            found.append(seen)
        else:
            _tally(stats["skipped"], seen)
    stats["kept"] = len(found)
    stats["scan_ms"], stats["search"] = round(scan[0] * 1000.0, 1), way[0]
    return found, stats, Sighting(frozenset(seen.name for seen in found).union(alive_known), frozenset(dead),
                                  tuple((seen.name, seen.definition, seen.zone_path, seen.at) for seen in found),
                                  tuple(killed), tuple(by_other))


def everyone(found: list[Seen], here: tuple | None, limit: int, within_m: float | None = None) -> list[Seen]:
    """Every enemy kept whose place is known, of every team, nearest the hunter first, at most limit, and within
    within_m of him when given. Every team at once (decision 31): trials 6a to 6n drew one team only, so that its
    enemies would not fight each other on the way; the horde is put in one team instead (decision 32)."""
    if here is None:
        return []
    near = [seen for seen in found if seen.at is not None
            and (within_m is None or math.dist(seen.at, here) <= within_m * 100.0)]
    return sorted(near, key=lambda seen: math.dist(seen.at, here))[:limit]
