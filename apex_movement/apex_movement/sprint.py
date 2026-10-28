"""Auto sprint: sprints while the move stick is fully pushed, on the ground, without aiming.

Ported from Auto Sprint 1.5.0, whose behaviour was verified in game on 2026-09-15. The game's 60 degree sprint limit
is kept (design decision 11). The ground speeds moved to ground_speed.py on 2026-09-18: they apply whether the auto
sprint is on or off.
"""

from typing import Any, Callable

from . import game, report, settings, walk_key

# Not a slider (spec, section 3): nobody needed to change Auto Sprint's value, and each slider can break the feel.
STICK_THRESHOLD = 0.95

_requested = False
_restarting = False
# Whether the game shows the third-person view on foot; the full pack gives the camera's reading (set_view), a separate
# file has no camera and stays in first person.
_third_person: Callable[[], bool] = lambda: False


def set_view(read: Callable[[], bool]) -> None:
    global _third_person
    _third_person = read


def reset() -> None:
    global _requested, _restarting
    _requested = _restarting = False


def _request(movement: Any, wanted: bool) -> None:
    global _requested
    movement.bWantsToSprint = wanted
    if wanted:
        movement.bWantsToStartSprinting = True
    # The game cancels sprint every frame in some states; only the mod's own on/off changes are logged.
    if wanted != _requested:
        report.note(f"sprint request {'on' if wanted else 'off'}")
    _requested = wanted


def refuse(movement: Any) -> bool:
    """Ends the sprint under way, the game's own included: the slow walk wins (Kevin, 2026-09-26). The one place
    that writes the sprint request, so the slow walk and the auto sprint never disagree on it."""
    if not movement.bWantsToSprint:
        return False
    _request(movement, False)
    return True


def update(character: Any, now_ns: int) -> None:
    global _restarting
    movement = character.CharacterMovement
    if _third_person() and settings.auto_sprint_third_person.value is not True:
        # Kevin, 2026-10-09: third-person moves are the same in every camera mod, and Apex Legends has no third
        # person: there the hunter sprints with the sprint key, as in Omni Sprint and Third Person & FOV, unless the
        # player turns auto sprint on for third person.
        if _requested:
            _request(movement, False)
        _restarting = False
        return
    aiming = game.is_aiming(character)
    pushed = game.stick(character) >= STICK_THRESHOLD
    walking = walk_key.walking()
    if movement.bIsSprinting:
        _restarting = False
    if not aiming and pushed and not walking and game.is_on_ground(movement):
        if not movement.bWantsToSprint:
            _request(movement, True)
        elif not movement.bIsSprinting and not character.bIsCrouched:
            # After a slide left to finish, sprint stops while bWantsToSprint stays set (2026-09-15): only a new
            # start request makes the game sprint again.
            movement.bWantsToStartSprinting = True
            if not _restarting:
                report.note("sprint restart")
            _restarting = True
    elif _requested and (aiming or not pushed or walking):
        _request(movement, False)


def stop(character: Any) -> None:
    # The walk key is not forgotten here: a movement of its own, it goes on without the auto sprint (Kevin,
    # 2026-09-25); the frame loop forgets it with the character, or when the whole mod stops.
    try:
        if character is not None and _requested:
            character.CharacterMovement.bWantsToSprint = False
    finally:
        reset()
