"""The one door between the grapple and what the player sees, owning no movement state: for each shot, the look
look_choice.py gives, the classic one (the game's gesture and rope, animation.py and beam.py) or the grapple gun's
(look_play.py, Vex only). A failure of either costs the visuals alone, never a pull; one of the grapple gun's gives way
to the classic look until the game restarts (look_choice.stop).
"""

from typing import Any

from . import animation, beam, game, hand_anchor, look_choice, look_load, look_play, report

_broken = False
_active = False
_ours = False


def reset() -> None:
    global _broken, _active, _ours
    _stop_classic()
    _drop_ours()
    _broken = _active = _ours = False
    animation.reset()
    beam.reset()
    hand_anchor.reset()


def start(character: Any, anchor: tuple, now_ns: int, flight_s: float) -> None:
    """Freezes this shot's look, so that menu edits cannot strand its rope or its hand pose."""
    global _active, _ours
    _active = _ours = False
    look = look_choice.for_shot(character)
    if look is None:
        return
    hand_anchor.reset()
    if look == look_choice.OURS:
        prepared = _guarded(lambda: look_play.prepare(character))
        if prepared and not look_play.ready():
            report.error_once("look:arms", "the first-person arms were not found: this shot takes the classic look")
        elif prepared and _guarded(lambda: look_play.start(character, anchor, now_ns, flight_s)):
            _ours = True
            report.note("look: grapple gun")
            return
    if _broken:
        return
    # Kevin keeps the combined hands and rope. Retired investigation values must have no effect.
    _active = True
    report.note("look: classic")
    animation.start()
    beam.start(character, anchor)


def follow(character: Any, anchor: tuple) -> None:
    """A missing hand transform must cost the visuals alone, even during hook flight. The grapple gun's look follows
    in tick."""
    global _broken
    if _broken or not _active:
        return
    try:
        beam.follow(game.hand_spot(character), anchor)
    except Exception as exc:
        _broken = True
        report.error_once("visuals:follow", f"grapple visuals switched off after an error: {exc!r}")
        _stop_classic()


def hold(character: Any, now_ns: int, start_gap: float, near: float, pull_cap: float) -> None:
    """The hook bites: the grapple gun's look gets the pull's numbers; the classic hand holds its pose."""
    if _ours:
        _guarded(lambda: look_play.catch(character, now_ns, start_gap, near, pull_cap))
    elif not _broken and _active:
        animation.hold()


def pulled(to_anchor: tuple, velocity: tuple) -> None:
    """A frame of the pull, numbers only, for the grapple gun's gestures."""
    if _ours:
        look_play.pulled(to_anchor, velocity)


def stop(now_ns: int) -> None:
    """The shot ends: the classic look goes at once, the grapple gun's ends its own way."""
    global _ours
    if not _ours:
        _stop_classic()
        return
    _ours = False
    _guarded(lambda: look_play.end(game.character(), now_ns))


def tick(character: Any, now_ns: int) -> None:
    """Every frame, shot or not: the grapple gun's shots and pieces while it is the look or a shot of it still runs,
    removed once it is not."""
    if look_play.busy() or look_choice.for_shot(character) == look_choice.OURS:
        _guarded(lambda: look_play.tick(character, now_ns))
    elif look_play.built():
        _guarded(look_play.reset)


def _guarded(action) -> bool:
    """`action` of the grapple gun's look; on failure, everything it put is removed and the classic look takes over."""
    global _ours
    try:
        action()
        return True
    except look_load.Missing as missing:
        look_choice.stop(look_choice.MISSING, f"{missing}; all: {', '.join(missing.paths)}")
    except Exception as exc:
        look_choice.stop(look_choice.FAILED, repr(exc))
    _ours = False
    _drop_ours()
    return False


def _drop_ours() -> None:
    try:
        look_play.reset()
    except Exception as exc:
        report.error_once("look:remove", f"some of the grapple gun's pieces could not be removed: {exc!r}")


def _stop_classic() -> None:
    global _active
    _active = False
    animation.stop()
    beam.stop()
