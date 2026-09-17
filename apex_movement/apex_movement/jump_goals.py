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


def collect(movement: Any) -> dict[str, Any]:
    """jump type -> kept definition pointer, for the five types; raises if the game refuses one."""
    original = str(movement.CurrentJump.JumpType.TagName)
    found: dict[str, Any] = {}
    try:
        for jump_type in JUMP_TYPES:
            movement.SetCurrentJumpType(_tag(f"Movement.JumpType.{jump_type}"))
            found[jump_type] = movement.CurrentJump.JumpGoal
    finally:
        movement.SetCurrentJumpType(_tag(original))
    return found
