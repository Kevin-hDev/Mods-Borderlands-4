"""Writes one line per jump: what kind it was, how fast it left the ground, what ground that was, and how high it got.

Kevin, 2026-09-17: on a raised wooden floor, on stairs and on one particular rocky slope, a sprint jump goes very low,
while the same jump without sprinting is fine. Elsewhere, including the same slope taken by the path, it is fine.

Nothing in the log could tell those apart: the jump budget only writes a line when the count or the type changes in the
air, so the type a jump leaves the ground with was never written at all — SprintJump appears nowhere in a whole
session. This writes the take-off, with the floor's own name, and the rise when the fall begins, which is what tells
one floor from another.
"""

from typing import Any

from . import game, report

# Bounded: a line per jump and a line per apex, which a session of jumping keeps to a few hundred.
MAX_JUMPS = 400

_floor = ""
_speed = 0.0
_start_z = 0.0
_top_z = 0.0
_airborne = False
_jumps = 0


def reset() -> None:
    global _floor, _speed, _start_z, _top_z, _airborne, _jumps
    _floor, _speed, _start_z, _top_z, _airborne, _jumps = "", 0.0, 0.0, 0.0, False, 0


def update(character: Any, now_ns: int) -> None:
    global _floor, _speed, _start_z, _top_z, _airborne, _jumps
    movement = character.CharacterMovement
    if game.is_on_ground(movement):
        if _airborne:
            _airborne = False
            report.note(f"jump landed rise={_top_z - _start_z:.0f}")
        _floor, _speed = _standing_on(movement), game.horizontal_speed(movement)
        return
    if _airborne:
        _top_z = max(_top_z, game.altitude(character))
        return
    _airborne, _start_z, _top_z = True, game.altitude(character), game.altitude(character)
    if _jumps >= MAX_JUMPS:
        return
    _jumps += 1
    report.note(f"jump take-off type={game.jump_type(movement)} vz={float(movement.Velocity.Z):.0f} "
                f"speed={_speed:.0f} floor={_floor}")


def _standing_on(movement: Any) -> str:
    """The floor the character stands on, by name; unknown rather than an error, it only serves the log."""
    try:
        return str(movement.CurrentFloor.HitResult.Component.Name)
    except Exception:
        return "?"
