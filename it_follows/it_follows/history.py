"""The last runs, most recent first (decision 49): for each, when it began, its level, the time limit chosen, the time
held, the kills, the deaths, and how it ended. kept.py keeps them from one game launch to the next, in this layout,
which carries its version from the first save.

The read is tolerant: a value edited by hand, or written by a later version, never keeps the window from opening.
Unknown fields are ignored; a malformed run is left out and counted for the log; past the cap, the oldest are cut; a
value that is not a mapping at all reads as no run, and says why.
"""

from typing import Any, NamedTuple

MAX_RUNS = 20
VERSION = 1
# 2100-01-01 in seconds: a later moment is not one the mod wrote.
MAX_WHEN = 4_102_444_800
# Bounds a read value must keep: a day held, ten million kills; beyond, the file was not written by the mod.
MAX_PLAYED_S = 86_400
MAX_COUNT = 10_000_000
MAX_LEVEL = 1_000
# How a run ends, as the history names it (decision 51): its time up, STOP, the game left, the mod turned off, or the
# run stopping by itself (the lent zone lost, an error in a sample).
ENDS = ("time_up", "stopped", "left_game", "mod_disabled", "interrupted")


class Run(NamedTuple):
    # Seconds since 1970, as time.time() gives them, cut to whole seconds.
    when: int
    level: int
    # The time limit chosen, None for none.
    limit_s: int | None
    played_s: int
    kills: int
    deaths: int
    end: str


def end_of(reason: str) -> str:
    """The end the history names for a run's stop reason (session.stop)."""
    return reason if reason in ENDS else "interrupted"


def record(runs: tuple[Run, ...], run: Run) -> tuple[Run, ...]:
    """The runs with this one on top, the oldest past MAX_RUNS dropped."""
    return ((run,) + runs)[:MAX_RUNS]


def encode(runs: tuple[Run, ...]) -> dict:
    return {"version": VERSION, "runs": [run._asdict() for run in runs]}


def _whole(value: Any, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _run(value: Any) -> Run | None:
    """The run, or None when it is malformed."""
    if not isinstance(value, dict):
        return None
    fields = {name: value.get(name) for name in Run._fields}
    limit = fields["limit_s"]
    if not (_whole(fields["when"], 0, MAX_WHEN) and _whole(fields["level"], 1, MAX_LEVEL)
            and (limit is None or _whole(limit, 1, MAX_PLAYED_S)) and _whole(fields["played_s"], 0, MAX_PLAYED_S)
            and _whole(fields["kills"], 0, MAX_COUNT) and _whole(fields["deaths"], 0, MAX_COUNT)
            and fields["end"] in ENDS):
        return None
    return Run(**fields)


class Loaded(NamedTuple):
    runs: tuple[Run, ...]
    # How many runs were malformed or past the cap, and left out.
    repaired: int = 0
    # Why the whole value was set aside, "" when it was read.
    unreadable: str = ""


def decode(value: Any) -> Loaded:
    """What the settings hold; no run when the value was never written ({})."""
    if not isinstance(value, dict):
        return Loaded((), unreadable=f"not a mapping ({type(value).__name__})")
    listed = value.get("runs", [])
    if not isinstance(listed, list):
        return Loaded((), repaired=1)
    runs = tuple(run for run in map(_run, listed[:MAX_RUNS]) if run is not None)
    return Loaded(runs, repaired=len(listed) - len(runs))
