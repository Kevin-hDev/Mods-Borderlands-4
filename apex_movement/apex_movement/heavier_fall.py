"""Heavier fall (spec 2.5): a stronger gravity, every jump kept at its height, plus Kevin's extra height.

Measured on 2026-09-16 (23:36) with GravityScale 1.3: every jump type lost height (normal 198 -> 147, double
225 -> 164-173) and the game never changed GravityScale during a jump. The times to the apex match the game solving
the rising gravity from GoalHeight: normal jump sqrt(2H / g) / scale = 489 ms, sprint 2H / (v scale) = 414 ms against
410 measured, double 368 against 365. So each jump reaches GoalHeight / scale, and writing GoalHeight x scale keeps
the height. A jump that also uses InitialZVelocity gets it x sqrt(scale) too, so every jump rises in 1 / sqrt(scale)
of its time like the normal jump does, instead of some jumps feeling lighter than others.
"""

import math
from typing import Any

from . import game, jump_goals, ownership, report, settings

GRAVITY_KEY = "movement.GravityScale"
FIELDS = ("GoalHeight", "InitialZVelocity")

_goals: dict[str, Any] = {}


def reset() -> None:
    _goals.clear()


def _key(jump_type: str, field: str) -> str:
    return f"JumpGoal_{jump_type}.{field}"


def _game_value(key: str, goal: Any, field: str) -> float:
    return float(ownership.original(key)) if ownership.is_owned(key) else float(getattr(goal, field))


def _write(key: str, scope: str, target: Any, field: str, value: float) -> bool:
    def read() -> float:
        return float(getattr(target, field))

    def put(new: float) -> None:
        setattr(target, field, new)

    if abs(read() - value) <= 0.01:
        ownership.claim(key, scope, read, put)
        return False
    ownership.write(key, scope, read, put, value)
    return True


def _apply_goal(jump_type: str, goal: Any, scale: float, extra: float) -> bool:
    height_key = _key(jump_type, "GoalHeight")
    # Kevin, 2026-09-17: the extra height goes to every jump type ("+20 partout pour tous les différents sauts").
    height = _game_value(height_key, goal, "GoalHeight") + extra
    changed = _write(height_key, ownership.ASSET, goal, "GoalHeight", height * scale)
    if goal.bUseInitialZVelocity:
        velocity_key = _key(jump_type, "InitialZVelocity")
        velocity = _game_value(velocity_key, goal, "InitialZVelocity")
        changed = _write(velocity_key, ownership.ASSET, goal, "InitialZVelocity", velocity * math.sqrt(scale)) or changed
    return changed


def update(character: Any, now_ns: int) -> None:
    movement = character.CharacterMovement
    if not _goals:
        # Changing the current jump type mid-air could disturb the jump in progress: definitions are read standing.
        if not game.is_on_ground(movement):
            return
        _goals.update(jump_goals.collect(movement))
    scale = float(settings.fall_weight.value)
    extra = float(settings.jump_height_bonus.value)
    changed = [jump_type for jump_type, goal in _goals.items() if _apply_goal(jump_type, goal, scale, extra)]
    if _write(GRAVITY_KEY, ownership.CHARACTER, movement, "GravityScale", scale) or changed:
        report.note(f"fall weight {scale:.2f} extra jump height {extra:.0f} jumps rewritten={','.join(changed) or '-'}")


def stop(character: Any) -> None:
    # Known limit: switched off in mid-air, the jump under way left with its speed x sqrt(scale) and finishes under the
    # game's gravity, so it rises higher once (the review's estimate: up to `scale` times; not measured in game).
    # Putting the gravity back at the next landing instead would need frames after stop, and the frame loop no longer
    # updates a stopped movement: the heavier gravity would then stay with the switch off, worse than one high jump.
    reset()
    owned = ownership.is_owned(GRAVITY_KEY)
    keys = [_key(jump_type, field) for jump_type in jump_goals.JUMP_TYPES for field in FIELDS]
    failures = ownership.restore_each([*keys, GRAVITY_KEY])
    if failures:
        # Raised once every key was tried: the frame loop reports it, and ownership keeps what is not back yet.
        raise RuntimeError("; ".join(failures))
    if owned:
        report.note("heavier fall off, game gravity and jumps restored")
