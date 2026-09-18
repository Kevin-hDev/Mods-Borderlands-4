"""The ground speeds: walking and sprinting, written every frame through the floor the game obeys.

Kevin, 2026-09-18: the Nexus page announces the raised speeds as their own entry, apart from the auto sprint. Until
now both lived in sprint.py, behind the auto sprint switch, so turning the auto sprint off quietly gave the game's
own speeds back as well — the page would have promised something the mod did not do.

Speed goes through MinAnalogWalkSpeed, the floor the game obeys over its own max speed (verified in game 2026-09-15).
"""

from typing import Any

from . import ownership, report, speed_order

FLOOR_KEY = "movement.MinAnalogWalkSpeed"


def reset() -> None:
    """Nothing of its own to forget: the game's floor belongs to ownership, which stop gives back."""


def _set_floor(movement: Any, speed: float) -> None:
    if abs(float(movement.MinAnalogWalkSpeed) - speed) <= ownership.SPEED_TOLERANCE:
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
    speeds = speed_order.speeds()
    _set_floor(movement, speeds.sprint if movement.bIsSprinting else speeds.walk)


def stop(character: Any) -> None:
    ownership.restore(FLOOR_KEY)
