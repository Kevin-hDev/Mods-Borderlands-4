"""Reaches every jump definition before any jump starts.

Verified in game on 2026-09-16 (23:31): after SetCurrentJumpType(tag), CurrentJump.JumpGoal is that type's
definition, and a kept pointer reads and writes the game's shared definition. GetJumpGoalForJumpType and
FGbxDefPtr(name, type) only gave empty pointers. The original jump type is put back before returning.
"""

from typing import Any

import unrealsdk

JUMP_TYPES = ("DefaultJump", "SprintJump", "DoubleJump", "SlideJump", "UpwardLadderJump")


def _tag(tag_name: str) -> Any:
    return unrealsdk.make_struct("GameplayTag", TagName=tag_name)


def _checked(jump_type: str, goal: Any, seen: dict[str, str]) -> Any:
    """The definition, once it reads and belongs to no other type seen so far; raises otherwise."""
    try:
        float(goal.GoalHeight)
    except AttributeError as exc:
        # An unresolved pointer has no fields to read (AttributeError, seen on 2026-09-16 at 23:24).
        raise ValueError(f"jump type {jump_type} gave an empty definition") from exc
    # Every read gives a new Python object, so identity tells nothing; the pointer's text names the definition
    # (FGbxDefPtr('JumpGoal_Sprint', 'JumpGoalDef', {...}), same log). A definition kept for two types would get the
    # extra height twice, and the second type's "game value" would be the first one's rewritten value.
    text = repr(goal)
    if text in seen:
        raise ValueError(f"jump types {seen[text]} and {jump_type} gave the same definition")
    seen[text] = jump_type
    return goal


def collect(movement: Any) -> dict[str, Any]:
    """jump type -> kept definition pointer, for the five types; raises if the game refuses one, gives an empty one,
    or gives one already given for another type."""
    original = str(movement.CurrentJump.JumpType.TagName)
    found: dict[str, Any] = {}
    seen: dict[str, str] = {}
    try:
        for jump_type in JUMP_TYPES:
            movement.SetCurrentJumpType(_tag(f"Movement.JumpType.{jump_type}"))
            found[jump_type] = _checked(jump_type, movement.CurrentJump.JumpGoal, seen)
    finally:
        movement.SetCurrentJumpType(_tag(original))
    return found
