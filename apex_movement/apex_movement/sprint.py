"""Auto sprint: sprints while the move stick is fully pushed, on the ground, without aiming.

Ported from Auto Sprint 1.5.0, whose behaviour was verified in game on 2026-09-15. The game's 60 degree sprint limit
is kept (design decision 11). The ground speeds moved to ground_speed.py on 2026-09-18: they apply whether the auto
sprint is on or off.
"""

from typing import Any

from . import game, report

# Not a slider (spec, section 3): nobody needed to change Auto Sprint's value, and each slider can break the feel.
STICK_THRESHOLD = 0.95

_requested = False
_restarting = False


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


def update(character: Any, now_ns: int) -> None:
    global _restarting
    movement = character.CharacterMovement
    aiming = game.is_aiming(character)
    pushed = game.stick(character) >= STICK_THRESHOLD
    if movement.bIsSprinting:
        _restarting = False
    if not aiming and pushed and game.is_on_ground(movement):
        if not movement.bWantsToSprint:
            _request(movement, True)
        elif not movement.bIsSprinting and not character.bIsCrouched:
            # After a slide left to finish, sprint stops while bWantsToSprint stays set (2026-09-15): only a new
            # start request makes the game sprint again.
            movement.bWantsToStartSprinting = True
            if not _restarting:
                report.note("sprint restart")
            _restarting = True
    elif _requested and (aiming or not pushed):
        _request(movement, False)


def stop(character: Any) -> None:
    if character is not None and _requested:
        character.CharacterMovement.bWantsToSprint = False
    reset()
