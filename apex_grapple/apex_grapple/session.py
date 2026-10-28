"""One transition and cleanup path for frame updates and input callbacks."""

from typing import Any

from . import aim, game, game_grapple, report

_seen_context: Any = None
_was_ready = False
_cleanup_pending = False


def cleanup(*operations: Any) -> bool:
    """Attempt every release even if an earlier SDK operation fails."""
    succeeded = True
    for operation in operations:
        try:
            operation()
        except Exception:
            succeeded = False
            report.error_once("session:cleanup", "grapple cleanup could not finish; it will be retried")
    return succeeded


def reset(rope: Any) -> bool:
    global _cleanup_pending
    from . import keys
    keys.forget_input()
    _cleanup_pending = not cleanup(lambda: rope.reset(), aim.reset, game_grapple.reset)
    return not _cleanup_pending


def refresh(now_ns: int, rope: Any, at_once: bool = False) -> Any:
    """Keys force a possession check before touching the rope; frames use the same transition."""
    global _seen_context, _was_ready
    try:
        pc = game.controller()
        # Possession is cheap to compare on every callback; mesh lookup keeps its normal interval.
        possession_changed = getattr(pc, "OakCharacter", None) != game.character()
        game.refresh(now_ns, at_once=at_once or possession_changed)
        character = game.character()
        context = game.context()
        ready = (character is not None and character == getattr(pc, "OakCharacter", None)
                 and game.anim() is not None and getattr(pc, "PlayerInput", None) is not None)
    except Exception:
        reset(rope)
        raise
    # The acknowledgement survives other callers refreshing game first, without owning a second cache.
    if context is not _seen_context or (_was_ready and not ready) or _cleanup_pending:
        from . import control_window
        control_window.cancel_for_gameplay()
        if not reset(rope):
            return None
    _seen_context, _was_ready = context, ready
    return character if ready else None
