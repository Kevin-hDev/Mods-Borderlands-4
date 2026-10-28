"""What follows the end of a run (decisions 49, 51 and 63): the run goes on top of the history (kept.py), and its
result waits for the window (panel_result.py). At the end of its time the window opens by itself on it (decision 63);
after STOP, pressed in the window, it shows there; after a run that stopped by itself, at the window's next opening,
so that the player learns why the enemies stopped coming. A run ended by leaving the game or turning the mod off
shows nothing: the player did it, and the history keeps it. Without his character, while he drives, the window is not
opened by itself: it could not pause the game (game_pause.hold, trial 9: no character in a vehicle), and would take
the mouse and keys from a vehicle still rolling (audit of 15 October 2026); the result waits for F5.
"""

from typing import Any

from . import history, kept, presence, report

# The result the window has still to show, None once shown.
_waiting: dict[str, history.Run | None] = {"run": None}
SHOWN_ENDS = ("time_up", "stopped", "interrupted")


def ended(run: Any, began: int, reason: str) -> history.Run:
    """The run just stopped for reason (session.stop), begun at began (seconds since 1970): kept, and its result
    waiting for the window; the window opened on it when its time is up."""
    clock, counts = getattr(run, "clock", None), getattr(run, "stats", None)
    limit = run.settings.duration_s
    done = history.Run(when=began, level=run.level.target, limit_s=None if limit is None else int(limit),
                       played_s=int(clock.played) if clock is not None else 0,
                       kills=counts.kills if counts is not None else 0,
                       deaths=counts.deaths if counts is not None else 0, end=history.end_of(reason))
    report.note("history_added", saved=kept.add(done), end=done.end)
    if done.end in SHOWN_ENDS:
        _waiting["run"] = done
    if done.end == "time_up":
        _open()
    return done


def _open() -> None:
    """The window opened on the result, from the run's last second; a window that cannot open now (the game's map or
    pause menu holds the cursor), or the player without his character, shows it at its next opening."""
    try:
        seat = presence.look()
        if seat.player is None:
            report.note("result_window_waits", why=seat.why)
            return
        from . import control_window
        control_window.start()
    except Exception as error:
        report.note("result_window_failed", error=type(error).__name__)


def waiting() -> history.Run | None:
    return _waiting["run"]


def shown() -> None:
    _waiting["run"] = None
