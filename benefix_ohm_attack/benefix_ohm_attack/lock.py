"""The lock: the beam takes the enemy it has touched long enough and stays on it while the aim strays.

The game's weapon the mod is named after does it (Kevin, 2026-10-02: "le rayon tient sur l'ennemi même quand le
viseur commence à se détacher de lui"). Its settings, read in the game's files that day
(docs/attaque-rayon/enquetes/2026-10-02-accroche-du-rayon.md): a lock after 0.2 s of contact, broken 30 degrees
away. What each of the game's settings does exactly is deduced from its name; this is the mod's own lock, on the
mod's own beam, with those two numbers as its defaults.

A locked enemy is held weakly, with the spot of its body the beam was on: that spot follows it. The lock lets go
when the aim strays past the angle, when the enemy dies or leaves the world, or when something stands between the
camera and it. Aimed straight at another enemy for the time of a contact, it moves to that one. A friend of the
player (his own familiar) and a dead enemy are never locked.

The lock is an extra: one that fails says so once and leaves the shot going on the enemy the aim is on, as before
the lock, until the mod is switched on anew.
"""

import math
from typing import Any, NamedTuple

from unrealsdk import unreal

from . import aim, enemy, report

# The ray that checks the way to a locked enemy ends this far past its spot; a thing met less than this before the
# spot is on the enemy (its shield, its weapon) and does not break the lock.
SIGHT_MARGIN = 50.0
# Frame times added up fall a hair short of the contact they make.
ROUNDING_S = 1e-9


class Target(NamedTuple):
    """Who the beam is on this frame: the enemy, the spot the beam ends at, the game's answer for the hits, and
    for a locked one how many degrees the aim is away from that spot."""

    enemy: Any
    point: tuple[float, float, float]
    hit: Any
    species: str
    distance: float
    locked: bool = False
    strayed: float = 0.0


_held: Any = None
_offset = (0.0, 0.0, 0.0)
_hit: Any = None
_species = ""
# The enemy the aim is on and not locked: for how long, and whether it may be locked at all.
_touched: Any = None
_touched_s = 0.0
_lockable = False
# One line of the log per shot for its first lock, one for its first loss: the proof it works, without a flood.
_lock_said = False
_loss_said = False
_refused = False


def forget() -> None:
    """Called at each new shot and at its end: nobody is locked, nothing is said yet."""
    global _held, _hit, _touched, _lock_said, _loss_said
    _held = _hit = _touched = None
    _lock_said = _loss_said = False


def restart() -> None:
    """Called when the mod is switched on: a lock that failed is tried again."""
    global _refused
    forget()
    _refused = False


def held() -> bool:
    return _held is not None


def plain(aimed: aim.Aim) -> Target | None:
    """The target without a lock: the enemy the aim is on, nobody otherwise."""
    if aimed.enemy is None:
        return None
    return Target(aimed.enemy, aimed.anchor, aimed.hit, aimed.species, aimed.distance)


def _release(reason: str) -> None:
    global _held, _hit, _loss_said
    _held = _hit = None
    if not _loss_said:
        _loss_said = True
        report.note(f"lock lost: {reason}")


def _kept(character: Any, start: tuple, way: tuple, break_deg: float) -> Target | None:
    """The locked enemy, when the lock still holds this frame."""
    global _hit
    if _held is None:
        return None
    actor = _held()
    if actor is None:
        return _release("the enemy left the world")
    if enemy.dead(actor):
        return _release("the enemy died")
    where = enemy.place(actor)
    if where is None:
        return _release("the enemy cannot be placed")
    point = tuple(where[axis] + _offset[axis] for axis in range(3))
    line = tuple(point[axis] - start[axis] for axis in range(3))
    distance = math.sqrt(sum(part * part for part in line))
    if distance <= 0.0:
        return _release("the enemy is on the camera")
    cosine = sum(line[axis] * way[axis] for axis in range(3)) / distance
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    if angle > break_deg:
        return _release(f"aim {angle:.0f} degrees away")
    beyond = tuple(point[axis] + line[axis] / distance * SIGHT_MARGIN for axis in range(3))
    met, result = aim.ray(character, start, beyond)
    if met:
        if aim.hit_actor(result) == actor:
            _hit = result
        elif float(result.Distance) < distance - SIGHT_MARGIN:
            return _release("something stands in the way")
    return Target(actor, point, _hit, _species, distance, True, angle)


def _contact(character: Any, other: Any, passed: float) -> float | None:
    """For how long the aim has stayed on that enemy; None for one that is never locked."""
    global _touched, _touched_s, _lockable
    known = _touched() if _touched is not None else None
    if known is None or known != other:
        _touched, _touched_s = unreal.WeakPointer(other), 0.0
        _lockable = not enemy.dead(other) and not enemy.friend(character, other)
    else:
        _touched_s += passed
    return _touched_s if _lockable else None


def _take(aimed: aim.Aim) -> Target | None:
    global _held, _offset, _hit, _species, _touched, _lock_said
    where = enemy.place(aimed.enemy)
    if where is None:
        return None
    _held, _touched = unreal.WeakPointer(aimed.enemy), None
    _offset = tuple(aimed.anchor[axis] - where[axis] for axis in range(3))
    _hit, _species = aimed.hit, aimed.species
    if not _lock_said:
        _lock_said = True
        report.note(f"lock on {aimed.species} at {aimed.distance / 100:.0f} m")
    return Target(aimed.enemy, aimed.anchor, aimed.hit, aimed.species, aimed.distance, True)


def follow(pc: Any, character: Any, aimed: aim.Aim, passed: float, delay_s: float, break_deg: float) -> Target | None:
    """The frame's target: the locked enemy while the lock holds, else the enemy the aim is on, else nobody."""
    global _refused
    if _refused:
        return plain(aimed)
    try:
        return _followed(pc, character, aimed, passed, delay_s, break_deg)
    except Exception as error:
        _refused = True
        forget()
        report.error_once("lock", f"the lock failed, the beam goes on without it: {error!r}")
        return plain(aimed)


def _followed(pc: Any, character: Any, aimed: aim.Aim, passed: float, delay_s: float,
              break_deg: float) -> Target | None:
    global _touched
    start, turn = aim.eye(pc)
    kept = _kept(character, start, aim.facing(turn), break_deg)
    other = aimed.enemy if aimed.enemy is not None and (kept is None or aimed.enemy != kept.enemy) else None
    if other is None:
        _touched = None
    else:
        lasted = _contact(character, other, passed)
        if lasted is not None and lasted >= delay_s - ROUNDING_S:
            kept = _take(aimed) or kept
    return kept if kept is not None else plain(aimed)
