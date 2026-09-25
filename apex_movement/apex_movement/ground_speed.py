"""The ground speeds: walking and sprinting, written every frame through the floor the game obeys.

Kevin, 2026-09-18: the Nexus page announces the raised speeds as their own entry, apart from the auto sprint. Until
now both lived in sprint.py, behind the auto sprint switch, so turning the auto sprint off quietly gave the game's
own speeds back as well — the page would have promised something the mod did not do.

Speed goes through MinAnalogWalkSpeed, the floor the game obeys over its own max speed (verified in game 2026-09-15).
The floor only raises that speed, so the walk key's slower walk also lowers the character's speed scale, which the
game multiplies the stance's speed by: 300 held in game at 300 / 470, with no write undone by the game in 8 s of
walking (2026-09-25). The stance speed gave 300 too, but every character of the machine shares it, a co-op guest
included; the scale belongs to this character alone.
"""

from typing import Any

from . import ownership, report, speed_order, walk_key

FLOOR_KEY = "movement.MinAnalogWalkSpeed"
# The stances whose speed the scale multiplies into the key's: standing, and falling, since the game caps the air speed
# at the falling stance's 470 x the scale; put back in the air, a jump from the key's walk reached 540 (audit,
# 2026-09-25). A crouch keeps the game's own scale and speed.
SCALED_STANCES = ("Stance_Player_Default", "Stance_Player_Falling")


def reset() -> None:
    """Nothing of its own to forget: the game's floor and scale belong to ownership, which stop gives back."""


def _set_floor(movement: Any, speed: float) -> None:
    def read() -> float:
        return float(movement.MinAnalogWalkSpeed)

    def put(value: float) -> None:
        movement.MinAnalogWalkSpeed = value

    if abs(read() - speed) <= ownership.SPEED_TOLERANCE:
        ownership.claim(FLOOR_KEY, ownership.CHARACTER, read, put)
        return
    ownership.write(FLOOR_KEY, ownership.CHARACTER, read, put, speed)
    report.note(f"ground speed {speed:.0f}")


def _set_scale(movement: Any, scale: float) -> None:
    speed_scale = movement.MaxGroundSpeedScale

    def read() -> float:
        return float(speed_scale.Value)

    def put(value: float) -> None:
        speed_scale.Value = value

    # Whenever the game computes its own again, aiming for one, the key's is written back, and the game's becomes the
    # value to put back.
    if ownership.adopt_game_value(speed_order.SCALE_KEY, ownership.TOLERANCE):
        report.note(f"speed scale of the game now {read():.3f}")
    if abs(read() - scale) <= ownership.TOLERANCE:
        ownership.claim(speed_order.SCALE_KEY, ownership.CHARACTER, read, put)
        return
    ownership.write(speed_order.SCALE_KEY, ownership.CHARACTER, read, put, scale)
    report.note(f"speed scale {scale:.3f}")


def _scaled_stance_speed(character: Any) -> float | None:
    stance = character.ReplicatedStance.stance
    return float(stance.speed) if str(stance._name) in SCALED_STANCES else None


def update(character: Any, now_ns: int) -> None:
    movement = character.CharacterMovement
    speeds = speed_order.speeds()
    stance_speed = None
    if movement.bIsSprinting:
        speed = speeds.sprint
    elif walk_key.asked():
        # Asked by the auto sprint while the walk key is held; stopped, it asks nothing.
        speed = speed_order.walk_key_speed()
        stance_speed = _scaled_stance_speed(character)
    else:
        speed = speeds.walk
    _set_floor(movement, speed)
    if stance_speed:
        _set_scale(movement, speed / stance_speed)
    else:
        ownership.restore(speed_order.SCALE_KEY)


def stop(character: Any) -> None:
    failures = ownership.restore_each((speed_order.SCALE_KEY, FLOOR_KEY))
    if failures:
        raise RuntimeError("; ".join(failures))
