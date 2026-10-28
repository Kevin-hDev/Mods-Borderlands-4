"""The slow walk as a movement: while the key walks, no sprint goes on, the game's own included.

Kevin, 2026-09-26: the slow walk wins over everything, the sprint and the normal walk alike, whatever the auto sprint
does; a player who sprints with the game's own key walks slowly all the same. The ground speed applies the key's
speed on its own; this module only ends the sprint, through the auto sprint, the one writer of the sprint request.

Toggled, two things end the walk without the key (Kevin, 2026-09-27, first trial in game): the sprint key, since a
toggled walk otherwise left no way to sprint but the key itself; and going down, since the frame loop sees no new
character at a death and the player came back walking slowly. Held, neither applies: the key is under the finger,
and its release ends the walk.

Full pack only (Kevin, 2026-09-26: the slow walk stays in Apex Movement, the complete mod, and the separate files
must be aligned with it): the key, the sprint it ends and the ground speed it slows are three movements, so a
separate file would show a slow walk that only half works.
"""

from typing import Any

from . import game, report, sprint, walk_key

_refused = False
# True once a frame of the walk has run: a sprint asked after that is the player's sprint key, not the sprint the
# walk found under way and ended when it began.
_walked = False


def reset() -> None:
    global _refused, _walked
    _refused = _walked = False


def _downed() -> bool:
    # The animation's own flag, True while the player fights for their life (verified in game, 2026-09-25,
    # docs/investigations/third_person_fov/camera/2026-09-25-ffyl-decalage-camera.md).
    return bool(getattr(game.anim(), "ATTRIBUTE_is_in_ffyl", False))


def _end(reason: str) -> None:
    walk_key.forget()
    report.note(f"slow walk ended: {reason}")
    reset()


def update(character: Any, now_ns: int) -> None:
    global _refused, _walked
    if not walk_key.walking():
        reset()
        return
    movement = character.CharacterMovement
    if walk_key.toggle.value is True:
        if _downed():
            _end("downed")
            return
        if _walked and movement.bWantsToSprint:
            _end("sprint asked")
            return
    _walked = True
    # One line per walk, not per frame: the game may ask its sprint again on every frame the sprint key is down.
    if sprint.refuse(movement) and not _refused:
        _refused = True
        report.note("sprint refused: slow walk")


def stop(character: Any) -> None:
    reset()
