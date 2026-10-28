"""The bounce: from the enemy the beam is on, a second beam to the nearest living foe around it.

The game's weapon the mod is named after chains to one more enemy (maxchains 1, taken within 20 m and let go past
25: maxchaindistance and chainbreakdistance, read in the game's files on 2026-10-02,
docs/attaque-rayon/enquetes/2026-10-02-accroche-du-rayon.md). Kevin asked for it with a switch the same day. This
is the mod's own: a second beam of the shot's element, and the shot's hits dealt to the second enemy as well.

Who is around is the foes' list (foes.py), walked once a second at most. Nothing checks that the way between the
two enemies is clear: a bounce can pass a wall.

The bounce is an extra: one that fails says so once and leaves the shot going without it, until the mod is switched
on anew.
"""

import math
from typing import Any, NamedTuple

from unrealsdk import unreal

from . import aim, beam, enemy, foes, lock, report

# The weapon's own: a second enemy is taken within 20 m of the spot the beam is on, and let go past 25 m.
TAKE, LET_GO = 2000.0, 2500.0
# The ray that finds the second enemy's skin starts this far from his middle, on the side of the first.
APPROACH = 150.0


class Second(NamedTuple):
    """The second enemy this frame: where its beam ends, and the game's answer for the hits when a ray gave one."""

    enemy: Any
    point: tuple[float, float, float]
    hit: Any
    species: str


_held: Any = None
_species = ""
_beam = beam.Beam("bounce beam")
_refused = False
# One line of the log per shot: the proof it works, without a flood.
_said = False


def forget() -> None:
    """Called at each new shot and at its end: nobody is held, the beam is removed."""
    global _held, _said
    _held = None
    _said = False
    _beam.off()


def restart() -> None:
    """Called when the mod is switched on: a bounce that failed is tried again."""
    global _refused
    forget()
    _refused = False


def _search(character: Any, first: lock.Target) -> Any:
    """The nearest living foe around the first enemy, held from now on; None when there is none."""
    global _held, _species, _said
    best = None
    for foe in foes.around(character):
        actor = foe.actor()
        where = enemy.place(actor) if actor is not None and actor != first.enemy else None
        if where is None:
            continue
        distance = math.dist(first.point, where)
        if distance > TAKE or (best is not None and distance >= best[0]):
            continue
        if enemy.dead(actor) or foe.friend(character):
            continue
        best = (distance, actor, foe.species)
    if best is None:
        return None
    distance, actor, _species = best
    _held = unreal.WeakPointer(actor)
    if not _said:
        _said = True
        report.note(f"bounce on {_species}, {distance / 100:.0f} m from the first")
    return actor


def _kept(first: lock.Target) -> Any:
    """The second enemy held, when he is still one: in the world, alive, near, and not the first himself."""
    actor = _held() if _held is not None else None
    if actor is None or actor == first.enemy or enemy.dead(actor):
        return None
    where = enemy.place(actor)
    return actor if where is not None and math.dist(first.point, where) <= LET_GO else None


def _skin(character: Any, origin: tuple, actor: Any, middle: tuple) -> tuple[tuple, Any]:
    """Where a ray coming from the first enemy touches the second, and its answer; his middle and no answer when
    the ray meets something else."""
    distance = math.dist(origin, middle)
    if distance <= 0.0:
        return middle, None
    back = min(distance, APPROACH) / distance
    start = tuple(middle[axis] + (origin[axis] - middle[axis]) * back for axis in range(3))
    met, result = aim.ray(character, start, middle)
    if met and aim.hit_actor(result) == actor:
        return aim.touched(result, middle), result
    return middle, None


def follow(character: Any, first: lock.Target | None, effect: beam.Effect) -> Second | None:
    """The frame's second enemy, its beam lit and moved; None, and no beam, when there is none."""
    global _refused
    try:
        return _followed(character, first, effect)
    except Exception as error:
        _refused = True
        forget()
        report.error_once("bounce", f"the bounce failed, the beam goes on without it: {error!r}")
        return None


def _followed(character: Any, first: lock.Target | None, effect: beam.Effect) -> Second | None:
    global _held
    actor = _kept(first) if first is not None else None
    found = False
    if actor is None:
        if _held is not None:
            _held = None
            _beam.off()
        if first is None or _refused:
            return None
        actor = _search(character, first)
        if actor is None:
            return None
        found = True
    middle = enemy.place(actor)
    if middle is None:
        return None
    point, hit = _skin(character, first.point, actor, middle)
    if found:
        _beam.light(character, effect, first.point, point)
    else:
        _beam.follow(first.point, point)
    return Second(actor, point, hit, _species)
