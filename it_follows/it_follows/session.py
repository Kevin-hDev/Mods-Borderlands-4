"""Starting and stopping It Follows' runs and its normal mode in a game session: the one run in progress, the camps kept
from one run to the next, the normal mode on, never both at once (decision 80), and why a start is refused, said to
the player as it is (spec, section 2).

A start is refused with a run already going, without a character (from a vehicle, or with no game loaded), and in a
game of several players. A start that raises gives back what it took and says so: the run is never left half made,
where the next Start would only answer that a run is going (trial 10's notes). A run that stops goes into the
history, and its result waits for the window (ending.py).
"""

import time

from typing import Any, NamedTuple

import mods_base

from . import camps, ending, frame, horde, presence, report
from .normal import mode as normal_mode, options as normal_options
from .run import Run

# The mod's camps, kept from one run to the next in a game session: a run would otherwise leave up to CROWD_MAX more
# in the world each time. The run in progress, None between two, and when it began, in seconds since 1970. The normal
# mode while it is on, None while it is off: never on during a run (decision 80).
_state: dict[str, Any] = {"pool": None, "run": None, "began": 0, "normal": None}
# The reasons a mode stops for when a second (frame.Beat) or an enemy's image (normal/enemy_time.py) raised.
ERRORS = ("error:", "time_error:")


def running() -> bool:
    return _state["run"] is not None


class Live(NamedTuple):
    """What the window shows of the run in progress (panel_run.py): its level, its time limit, the time played,
    the kills and the deaths."""
    level: int
    limit_s: float | None
    played_s: float
    kills: int
    deaths: int


def live() -> Live | None:
    """The run in progress as the window shows it, None between two runs."""
    run = _state["run"]
    if run is None:
        return None
    clock, counts = getattr(run, "clock", None), getattr(run, "stats", None)
    return Live(run.level.target, run.settings.duration_s, clock.played if clock is not None else 0.0,
                counts.kills if counts is not None else 0, counts.deaths if counts is not None else 0)


def start(settings: Any) -> str:
    """Starts a run with these settings (options.Settings): "started", or why not."""
    if running():
        return "already_running"
    if normal_on():
        return "normal_on"
    pc = mods_base.get_pc()
    player = getattr(pc, "OakCharacter", None) if pc is not None else None
    if player is None:
        if presence.in_vehicle(pc):
            report.said("No run from a vehicle: get out of it, then press Start.")
            return "in_vehicle"
        report.said("No run: load a game first.")
        return "no_character"
    players = presence.players()
    if players is not None and players > 1:
        report.said("The Horde only works in solo games for now. Your game is not changed.")
        return "coop"
    report.begin_run()
    if players is None:
        report.note("players_unknown")
    if _state["pool"] is None:
        _state["pool"] = camps.Camps(report.announce, horde.CROWD_MAX)
    run = Run(settings, pc, player, _state["pool"], stop)
    _state["run"], _state["began"] = run, int(time.time())
    try:
        outcome = run.begin(frame.now())
    except Exception as error:
        outcome = _failed(run, error)
    if outcome != "started":
        _state["run"] = None
    return outcome


def _failed(run: Run, error: Exception) -> str:
    """A start that raised: what it took given back, written down and said; quitting to the main menu puts the game
    back itself when that fails too (trial 7)."""
    report.note("start_failed", error=type(error).__name__)
    try:
        run.end("start_failed")
    except Exception as again:
        report.note("stop_failed", error=type(again).__name__)
        report.said("The run could not start, and what it changed could not all be given back. Quit to the main menu "
                    "and load your game again. The reason is in unrealsdk.log.")
        return "start_failed"
    report.said("The run could not start. What it had changed was given back. The reason is in unrealsdk.log.")
    return "start_failed"


def stop(reason: str = "stopped") -> str:
    """Stops the run in progress: "stopped", or "not_running"."""
    run, _state["run"] = _state["run"], None
    if run is None:
        return "not_running"
    run.end(reason)
    ending.ended(run, _state["began"], reason)
    return "stopped"


class NormalLive(NamedTuple):
    """What the window shows of the normal mode on (panel_normal.py): its level, and whether it plays in a game."""
    level: str
    playing: bool


def normal_on() -> bool:
    return _state["normal"] is not None


def normal_live() -> NormalLive | None:
    mode = _state["normal"]
    return None if mode is None else NormalLive(mode.settings.level.name, mode.playing())


def start_normal(settings: Any) -> str:
    """Turns the normal mode on (normal.options.Settings): "playing", "waiting" for a game, or why not: a Horde run
    going, the mode already on. A co-op guest plays the guest's part (normal/guest.py). From a vehicle or without a
    game it waits rather than refuse: on, it starts by itself in the next game anyway. A start that raises ends the mode and says so."""
    if running():
        return "horde_running"
    if normal_on():
        return "already_on"
    mode = normal_mode.Mode(settings, stop_normal)
    _state["normal"] = mode
    try:
        return mode.begin(frame.now())
    except Exception as error:
        report.note("normal_start_failed", error=type(error).__name__)
        stop_normal("start_failed")
        return "start_failed"


def stop_normal(reason: str = "stopped") -> str:
    """Turns the normal mode off: "stopped", or "not_on". A second or an image that raised says so to the player who
    reads the log, once what the mode changed is given back (spec, section 6), and writes the choice to be on off, as
    STOP does: the window then shows START, and the next launch does not turn on again a mode that failed (Kevin,
    15 October 2026, after the audit: « Ok on fait ca »)."""
    mode, _state["normal"] = _state["normal"], None
    if mode is None:
        return "not_on"
    mode.end(reason)
    if reason.startswith(ERRORS):
        report.note("normal_off_written", saved=_written_off())
        report.said("The normal mode stopped after an error. What it had changed was given back: your game is not "
                    "changed. Press Start to turn it on again. The reason is in unrealsdk.log.")
    return "stopped"


def _written_off() -> bool | str:
    """The normal mode's choice to be on written off in the settings file: True, or why not."""
    from . import mod

    normal_options.on.value = False
    try:
        mod.save_settings()
    except Exception as error:
        return f"failed:{type(error).__name__}"
    return True
