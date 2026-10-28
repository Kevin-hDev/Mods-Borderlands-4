"""The OPTIONS page's saturated colours (decision 149): off at first; on, every post process of the world that sets
the saturation has it multiplied by the chosen profile's factor (colours_game.py finds them).

Kevin, 19 October 2026: the photo mode's Saturation at 170 is the look (trial 116: the engine's 1.7); three profiles,
1.4, 1.7 and 2, the second at first. Multiplying keeps the game's own grading, and a volume that sets the saturation
within its bounds is raised as well, or the colours would fall back on entering it.

Each one's saturation is kept by its path: the game's own, and the one written. While on, a pass each second
(frame.Beat) reads them again: one still at what was written is left; one the game changed, or one streamed in, has
its value taken as the game's own and raised. Off, or the mod disabled, each one still at what was written gets the
game's own back; one the game changed since is left as the game made it. Nothing is saved: a relaunched game starts
from its own colours, and the row raises them again. A change in the window, its preview card's included
(panel_colours.py), is applied at once: the game stands paused behind the window, and the pass with it.
"""

from typing import Any

from mods_base import get_pc

from . import colours_game as game, frame, options, report

WATCH_ID = "it_follows:colours"
# Lines that say what a pass wrote, at most a launch: a game rewriting a saturation each second would fill the log.
MAX_NOTES = 40

# By path; each pass forgets what it did not find, so it holds no more than colours_game.MAX_FOUND.
_held: dict[str, dict] = {}
_state: dict[str, Any] = {"beat": None, "notes": 0}


def factor(on: bool, profile: Any) -> float | None:
    """The factor the rows ask for, None when off; a profile the settings file does not know reads as the default."""
    if not on:
        return None
    return options.COLOUR_PROFILES.get(profile, options.COLOUR_PROFILES[options.DEFAULT_COLOUR_PROFILE])


def _wanted(on: Any = None, profile: Any = None) -> float | None:
    """The factor the rows ask for, the value about to be set given instead of the row's own."""
    on = options.colours.value if on is None else on
    return factor(on is True, options.colour_profile.value if profile is None else profile)


def scaled(own: tuple, by: float) -> tuple:
    """The game's own saturation times the factor, its W kept, within the engine's bounds."""
    def bounded(value: float) -> float:
        return min(game.LARGEST, max(game.SMALLEST, value * by))

    return bounded(own[0]), bounded(own[1]), bounded(own[2]), own[3]


def apply(by: float | None) -> str:
    """One pass: every saturation of the world set for the factor, or given back for None; never raising."""
    try:
        return _apply(by)
    except game.SearchUnavailable as error:
        report.error_once("colours:search", f"Saturated colours paused: the game's search failed ({error})")
        return "no_search"
    except Exception as error:
        report.error_once(f"colours:{type(error).__name__}",
                          f"Saturated colours unchanged: {type(error).__name__}: {str(error)[:120]}")
        return "failed"


def _apply(by: float | None) -> str:
    pc = get_pc(possibly_loading=True)
    if pc is None:
        return "no_world"
    seen, written, refused = set(), 0, 0
    for item in game.found(pc):
        key = game.path(item)
        if key is None:
            continue
        seen.add(key)
        now = game.saturation(item)
        if not game.valid(now):
            # Bounded, a NaN would read as 0: a picture without colours.
            report.error_once("colours:unreadable", f"Saturated colours: a saturation left alone, unreadable: {now}")
            continue
        entry = _held.get(key)
        ours = entry is not None and game.same(now, entry["written"])
        own = entry["own"] if ours else now
        target = own if by is None else scaled(own, by)
        if by is None:
            _held.pop(key, None)
            if game.same(now, own):
                continue
        elif game.same(now, target):
            continue
        if game.write(item, target):
            written += 1
            if by is not None:
                _held[key] = {"own": own, "written": target}
        else:
            refused += 1
    for key in [key for key in _held if key not in seen]:
        del _held[key]
    if written or refused:
        _note(by, written, refused)
    return "given_back" if by is None else "raised"


def _note(by: float | None, written: int, refused: int) -> None:
    if _state["notes"] >= MAX_NOTES:
        return
    _state["notes"] += 1
    report.note("colours_written", factor=by, written=written, refused=refused, held=len(_held),
                last=_state["notes"] == MAX_NOTES)


def _tick(_moment: float) -> None:
    apply(_wanted())


def _watch_failed(reason: str) -> None:
    report.note("colours_watch_failed", reason=reason)
    _stop_watch()


def _follow(by: float | None) -> None:
    """The pass each second runs while a factor is wanted, and stops when none is."""
    if by is None:
        _stop_watch()
    elif _state["beat"] is None:
        beat = frame.Beat(_tick, _watch_failed, identifier=WATCH_ID)
        _state["beat"] = beat
        beat.start()


def _stop_watch() -> None:
    beat, _state["beat"] = _state["beat"], None
    if beat is not None:
        beat.stop()


def _set(by: float | None) -> None:
    apply(by)
    _follow(by)


def switched(_option: Any, value: Any) -> None:
    """The switch changed in the window (mods_base calls this before the value is set)."""
    _set(_wanted(on=value is True))


def chosen(_option: Any, value: Any) -> None:
    """The profile changed in the window (mods_base calls this before the value is set)."""
    _set(_wanted(profile=value))


def start() -> None:
    """The mod enabled, at launch too: the colours raised now if the switch is on, then each second."""
    _set(_wanted())


def stop() -> None:
    """The mod disabled: the pass stopped, the game's own colours back."""
    _stop_watch()
    apply(None)
