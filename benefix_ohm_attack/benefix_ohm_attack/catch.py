"""The catch: the foe near the aim's line the beam goes to when the aim itself is on nobody.

The game's weapon the mod is named after catches an enemy a hand's width from the crosshair (collisionradius 20,
docs/attaque-rayon/enquetes/2026-10-02-accroche-du-rayon.md). The mod first swept a ball along the aim for that
(the engine's SphereTraceSingle): the ball meets the ground before a low enemy, and one wider than the camera is
high starts inside the ground. Kevin, 2026-10-02, after his first trial: no difference to be seen between the
lowest and the highest setting, "permettre au réglage une limite bien plus importante". So the catch is measured
instead: of the foes known (foes.py), the one whose body passes nearest the aim's line, within the distance set, and
that a ray from the camera meets. Nothing but calls verified in game.

A body is taken as a man's: 30 cm about a line from 60 cm under its middle to 60 cm over it. A bigger one is caught
from nearer its middle than its skin.

The catch is an extra: one that fails says so once and leaves the aim as it is, until the mod is switched on anew.
"""

import math
from dataclasses import replace
from typing import Any

from . import aim, enemy, foes, report

BODY_HALF = 60.0
BODY_RADIUS = 30.0
# The ways to this many foes are tried in a frame: a ray each.
MAX_TRIED = 3

_refused = False


def restart() -> None:
    global _refused
    _refused = False


def _beside(start: tuple, way: tuple, middle: tuple, reach: float) -> float | None:
    """How far the aim's line passes from that body; None for one behind the camera or past the reach."""
    best = None
    for lift in (0.0, BODY_HALF, -BODY_HALF):
        to = (middle[0] - start[0], middle[1] - start[1], middle[2] + lift - start[2])
        along = sum(to[axis] * way[axis] for axis in range(3))
        if along <= 0.0 or along > reach:
            continue
        aside = math.sqrt(max(sum(part * part for part in to) - along * along, 0.0))
        best = aside if best is None else min(best, aside)
    return None if best is None else max(best - BODY_RADIUS, 0.0)


def _met(character: Any, start: tuple, actor: Any, middle: tuple, species: str) -> aim.Aim | None:
    """The aim on that foe, when a ray from the camera to his middle meets him."""
    met, result = aim.ray(character, start, middle)
    if not met or aim.hit_actor(result) != actor:
        return None
    distance, length = float(result.Distance), math.dist(start, middle)
    along = tuple(start[axis] + (middle[axis] - start[axis]) / length * distance for axis in range(3))
    return aim.Aim(anchor=aim.touched(result, along), hit=result, enemy=actor, species=species, distance=distance,
                   caught=True)


def _nearest(pc: Any, character: Any, aimed: aim.Aim, width: float, reach: float) -> aim.Aim:
    start, turn = aim.eye(pc)
    way = aim.facing(turn)
    within = []
    for foe in foes.around(character):
        actor = foe.actor()
        middle = enemy.place(actor) if actor is not None and not enemy.dead(actor) else None
        gap = _beside(start, way, middle, reach) if middle is not None else None
        if gap is not None and gap <= width:
            within.append((gap, foe, actor, middle))
    within.sort(key=lambda entry: entry[0])
    tried = 0
    for _gap, foe, actor, middle in within:
        if foe.friend(character):
            continue
        if tried == MAX_TRIED:
            break
        tried += 1
        found = _met(character, start, actor, middle, foe.species)
        if found is not None:
            return found
    return replace(aimed, hidden=True) if tried else aimed


def near(pc: Any, character: Any, aimed: aim.Aim, width: float, reach: float) -> aim.Aim:
    """The aim moved onto the foe nearest its line, when one stands within the distance; the aim as it is
    otherwise."""
    global _refused
    if _refused or width <= 0.0:
        return aimed
    try:
        return _nearest(pc, character, aimed, width, reach)
    except Exception as error:
        _refused = True
        report.error_once("catch", f"the catch failed, the beam goes where the aim is: {error!r}")
        return aimed
