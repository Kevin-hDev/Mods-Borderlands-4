"""Writes a line each time the game's controlled move changes: its network copy, the game's own answer, and where the
character is.

Kevin's séance 2 (2026-09-18): after a ground slam, every climb was refused as `game_move` for 25 s. Séance 3 showed
why: the copy keeps Move_GroundSlam after landing, through whole flights, until a slide replaces it. The climb now asks
the game instead (game.in_controlled_move), and séance 4 verified its answer: true during a slam, a slide and a dash,
false as soon as the slam lands. Kept for the game versions Kevin does not have, like jump_report: if an update changes
either side, these lines show it without a new session. It belongs to the wall climb, the movement that refuses on it.
"""

from typing import Any

from . import game, report

# Bounded: a move starts and clears a few times a minute, so a session writes a few hundred lines. Counted from the mod
# being switched on, not from the last level load.
MAX_LINES = 400

_last: tuple[str, bool] | None = None
_lines = 0


def reset() -> None:
    """A new character: say its move again, keep the count of lines written."""
    global _last
    _last = None


def stop(character: Any) -> None:
    global _lines
    reset()
    _lines = 0


def update(character: Any, now_ns: int) -> None:
    global _last, _lines
    movement = character.CharacterMovement
    seen = (game.controlled_move_name(movement), game.in_controlled_move(movement))
    if seen == _last:
        return
    _last = seen
    if _lines >= MAX_LINES:
        return
    _lines += 1
    name, performing = seen
    report.note(f"game controlled move {name or 'none'} performing={performing} mode={game.movement_mode(movement)}")
