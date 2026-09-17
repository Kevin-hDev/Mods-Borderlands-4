"""Auto sprint and ground speeds: sprints while the move stick is fully pushed, on the ground, without aiming.

Ported from Auto Sprint 1.5.0, whose behaviour was verified in game on 2026-09-15. Ground speed goes through the
MinAnalogWalkSpeed floor, which the game obeys over its own max speed; the game's 60 degree sprint limit is kept
(design decision 11).
"""

from typing import Any

from . import game, ownership, report, settings

# Not a slider (spec, section 3): nobody needed to change Auto Sprint's value, and each slider can break the feel.
STICK_THRESHOLD = 0.95
FLOOR_KEY = "movement.MinAnalogWalkSpeed"

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


def _update_request(character: Any, movement: Any) -> None:
    global _restarting
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


def _set_floor(movement: Any, speed: float) -> None:
    if abs(float(movement.MinAnalogWalkSpeed) - speed) <= 0.5:
        return
    ownership.write(
        FLOOR_KEY, ownership.CHARACTER,
        lambda: movement.MinAnalogWalkSpeed,
        lambda value: setattr(movement, "MinAnalogWalkSpeed", value),
        speed,
    )
    report.note(f"ground speed {speed:.0f}")


def update(character: Any, now_ns: int) -> None:
    movement = character.CharacterMovement
    _update_request(character, movement)
    speeds = settings.speeds()
    _set_floor(movement, speeds.sprint if movement.bIsSprinting else speeds.walk)


def stop(character: Any) -> None:
    if character is not None and _requested:
        character.CharacterMovement.bWantsToSprint = False
    reset()
    ownership.restore(FLOOR_KEY)
