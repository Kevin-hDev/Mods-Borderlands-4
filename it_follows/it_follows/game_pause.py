"""The game paused while It Follows' window is open in a game (decision 48: « Comme pour le mod BL4 Arena, quand le
joueur ouvre le menu, ça doit mettre le jeu en pause »): the one owner of that pause. The window holds it once open
(control_window.py) and its closing gives it back, tried again as its other resources are (control_window_cleanup.py).
Taken from BL4 Arena's game_pause.py, as It Follows keeps its own code (decision 45): a fault found in one is mended in
the other.

Paused with the player's controller and given back with the world, by GameplayStatics.SetGamePaused read back by
IsGamePaused (vérifié en jeu with BL4 Arena, solo). A game already paused, by the game or another mod, is left as it
is and never resumed here; one the game will not pause, an online game maybe (non vérifié), leaves the window open
over the running game.

Trial 17: the pause read back held at every opening, yet Kevin saw the game go on under the window. Why is not known.
So the window looks once a second whether the game still stands still (watch), pauses it again when it does not, and
the release says what the world's clocks did while the window was open: its time (stopped by a pause), its unpaused
time and the real time. The run's clock reads the world's time (clock.py), which stood still under the window at every
release of trials 18 to 32 while the other two ran on."""

import math
import time
from typing import Any

import mods_base
import unrealsdk
from unrealsdk.unreal import WeakPointer

from . import report

STATICS = "GameplayStatics"
# The world's clocks, read at the hold and at the release: what each did under the window is said in the log.
CLOCKS = {"world_s": "GetTimeSeconds", "unpaused_s": "GetUnpausedTimeSeconds", "real_s": "GetRealTimeSeconds"}
# How often watch reads the pause, in seconds: the window polls many times a second.
WATCH_EVERY_S = 1.0

# The world paused, held weakly, None while no pause is held; its clocks when the pause was taken; when watch last
# looked, on the real clock; how many times the game was found running under the window.
_held: dict = {"world": None, "clocks": None, "watched": 0.0, "lost": 0}
# The real clock, in seconds: the tests move it.
real_s = time.monotonic


def holding() -> bool:
    return _held["world"] is not None


def _paused(statics: Any, context: Any) -> bool:
    """IsGamePaused, read strictly: a value that is no bool raises rather than being taken for a pause."""
    value = statics.IsGamePaused(context)
    if isinstance(value, tuple) and len(value) == 1:
        value = value[0]
    if type(value) is not bool:
        raise ValueError(f"IsGamePaused gave {type(value).__name__}")
    return value


def _clocks(statics: Any, context: Any) -> dict | None:
    """The world's clocks, in seconds; None when one cannot be read."""
    try:
        read = {field: float(getattr(statics, name)(context)) for field, name in CLOCKS.items()}
    except Exception:
        return None
    return read if all(math.isfinite(value) for value in read.values()) else None


def _end(why: str, **fields: Any) -> None:
    _held.update(world=None, clocks=None, lost=0)
    report.note("pause", outcome=why, **fields)


def hold() -> bool:
    """The game paused, said; whether the window holds a pause. Never raises: the window opens either way."""
    if holding():
        return True
    try:
        pc = mods_base.get_pc()
        if pc is None or getattr(pc, "OakCharacter", None) is None:
            report.note("pause", outcome="not_in_game")
            return False
        statics = unrealsdk.find_class(STATICS).ClassDefaultObject
        if _paused(statics, pc):
            report.note("pause", outcome="paused_already")
            return False
        # Held before the call: paused, then raised, the pause is still given back.
        _held.update(world=WeakPointer(mods_base.ENGINE.GameViewport.World), clocks=_clocks(statics, pc),
                     watched=real_s(), lost=0)
        statics.SetGamePaused(pc, True)
        if not _paused(statics, pc):
            _end("refused")
            return False
        report.note("pause", outcome="held")
        return True
    except Exception as error:
        report.note("pause", outcome="failed", error=type(error).__name__, text=str(error)[:report.MAX_TEXT])
        if holding():
            release()
        return False


def watch() -> None:
    """While the window holds the pause, once a second: a game found running is paused again, said at the first time
    of each pause and counted for the release. Never raises."""
    reference = _held["world"]
    now = real_s()
    if reference is None or now - _held["watched"] < WATCH_EVERY_S:
        return
    _held["watched"] = now
    try:
        world = reference()
        if world is None:
            return
        statics = unrealsdk.find_class(STATICS).ClassDefaultObject
        if _paused(statics, world):
            return
        _held["lost"] += 1
        if _held["lost"] == 1:
            report.note("pause", outcome="lost")
        statics.SetGamePaused(mods_base.get_pc(), True)
    except Exception as error:
        report.error_once("pause:watch", f"pause: not watched ({type(error).__name__})")


def _under_window(statics: Any, world: Any) -> dict:
    """What each of the world's clocks did while the window held the pause, in seconds."""
    began, ended = _held["clocks"], _clocks(statics, world)
    if began is None or ended is None:
        return {"clocks": "unreadable", "lost": _held["lost"]}
    spent = {field: round(ended[field] - began[field], 2) for field in CLOCKS}
    return {**spent, "lost": _held["lost"]}


def release() -> bool:
    """The pause held given back, said; False while the game keeps it, so that the window's closing tries again.
    Never raises."""
    reference = _held["world"]
    if reference is None:
        return True
    try:
        world = reference()
        if world is None:
            _end("world_gone")
            return True
        statics = unrealsdk.find_class(STATICS).ClassDefaultObject
        if _paused(statics, world):
            statics.SetGamePaused(world, False)
        if _paused(statics, world):
            report.note("pause", outcome="kept_by_game")
            return False
        spent = _under_window(statics, world)
    except Exception as error:
        report.note("pause", outcome="release_failed", error=type(error).__name__, text=str(error)[:report.MAX_TEXT])
        return False
    _end("released", **spent)
    return True
