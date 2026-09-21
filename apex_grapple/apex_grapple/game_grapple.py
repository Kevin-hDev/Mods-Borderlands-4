"""Prototype switch: hand the grapple to the game, on a point the mod keeps under the aim.

While `ON` is True, the mod stops pulling. Every press goes to the game, which grapples with its own
rope, hand and hook to the point `game_target.py` keeps on the surface under the crosshair. The one
question this build answers: does the game grapple to a point the mod placed, rope and all?

If it does, the next build keeps the game's grapple and takes the pull back — the mod owns the
velocity during a pull already, and that part is validated (Kevin, 2026-09-20). If it does not,
`ON` goes back to False and the mod is exactly what it was.

Disposable as a switch: it becomes a proper setting, or it goes, once the answer is known.
"""

from typing import Any

from . import aim, game, game_target, settings

# Trial A isolates the beam's coordinate system and keeps Apex's own traction in charge.
ON = False
# How often the point is moved under the aim. A ray every frame is what Apex Movement already does;
# every 50 ms is plenty for a point the player cannot see move.
EVERY_NS = 50_000_000

_next_ns = 0


def reset() -> None:
    global _next_ns
    _next_ns = 0
    game_target.reset()


def aim_target(character: Any, now_ns: int) -> None:
    """Keeps the mod's point where the mod would grapple, and away from anything it would punch."""
    global _next_ns
    if not ON or now_ns < _next_ns:
        return
    _next_ns = now_ns + EVERY_NS
    looking = game.aim(character)
    if looking is None:
        game_target.follow(character, None)
        return
    start, facing = looking
    shot = aim.look(character, start, facing, float(settings.grapple_range.value),
                    ignore=game_target.held_list())
    wanted = aim.grapples(shot, float(settings.punch_range.value), bool(settings.melee_wins.value))
    game_target.follow(character, shot.anchor if wanted else None)
