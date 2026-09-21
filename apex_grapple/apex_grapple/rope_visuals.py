"""Coordinates the optional hands and beam without owning any movement state."""

from typing import Any

from . import animation, beam, game, hand_anchor, report, settings

_broken = False
_active = False


def reset() -> None:
    global _broken, _active
    stop()
    _broken = _active = False
    animation.reset()
    beam.reset()
    hand_anchor.reset()


def start(character: Any, anchor: tuple) -> None:
    global _active
    _active = False
    if _broken or not bool(settings.show_rope.value):
        return
    # Kevin keeps the combined hands and rope. Retired investigation values must have no effect.
    # Freeze visibility for this shot so menu edits cannot strand its beam or hand pose.
    _active = True
    hand_anchor.reset()
    animation.start()
    beam.start(character, anchor)


def follow(character: Any, anchor: tuple) -> None:
    """A missing hand transform must cost the visuals alone, even during hook flight."""
    global _broken
    if _broken or not _active:
        return
    try:
        beam.follow(game.hand_spot(character), anchor)
    except Exception as exc:
        _broken = True
        report.error_once("visuals:follow", f"grapple visuals switched off after an error: {exc!r}")
        stop()


def hold() -> None:
    """Restore the established hand pose: Kevin's requested investigation concerns the rope only."""
    if not _broken and _active:
        animation.hold()


def stop() -> None:
    global _active
    _active = False
    animation.stop()
    beam.stop()
