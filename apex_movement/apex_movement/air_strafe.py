"""Air strafe (spec 2.4): change direction in the air almost at once, as with Kevin's Player Movement settings.

In Unreal the acceleration in the air is MaxAcceleration x AirControl (engine knowledge, not verified in BL4), so both
come from the Player Movement settings file Kevin played with: AirControl 20 against the game's 0.6, and
MaxAcceleration from its slider, settings.air_acceleration, whose default is the value Kevin kept (2026-09-17: "pour
conserver quelques millisecondes d'accélération"). MaxAcceleration also sets how fast walking and sprinting start and
stop on the ground.
"""

from typing import Any

from . import ownership, report, settings

ACCELERATION_KEY = "movement.MaxAcceleration"
AIR_CONTROL_KEY = "movement.AirControl"
AIR_CONTROL = 20.0


def reset() -> None:
    pass


def _write(movement: Any, key: str, field: str, value: float) -> bool:
    if abs(float(getattr(movement, field)) - value) <= 0.01:
        return False
    ownership.write(key, ownership.CHARACTER, lambda: float(getattr(movement, field)),
                    lambda v: setattr(movement, field, v), value)
    return True


def update(character: Any, now_ns: int) -> None:
    movement = character.CharacterMovement
    acceleration = float(settings.air_acceleration.value)
    changed = _write(movement, ACCELERATION_KEY, "MaxAcceleration", acceleration)
    changed = _write(movement, AIR_CONTROL_KEY, "AirControl", AIR_CONTROL) or changed
    if changed:
        report.note(f"air strafe acceleration {acceleration:.0f} air control {AIR_CONTROL:.0f}")


def stop(character: Any) -> None:
    owned = ownership.is_owned(ACCELERATION_KEY) or ownership.is_owned(AIR_CONTROL_KEY)
    failures = ownership.restore_each((ACCELERATION_KEY, AIR_CONTROL_KEY))
    if failures:
        # Raised once both were tried: the frame loop reports it, and ownership keeps what is not back yet.
        raise RuntimeError("; ".join(failures))
    if owned:
        report.note("air strafe off, game acceleration and air control restored")
