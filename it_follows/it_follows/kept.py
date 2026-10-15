"""The last runs, kept from one game launch to the next (decision 49): one hidden option of the mod's settings file, in
history.py's layout, which the SDK writes whole through the writer every one of our mods shares
(settings_persistence.py), as BL4 Arena keeps its launches. The one owner of that option: read once when the mod
starts, written again at the end of each run.

Written at the run's end rather than when the window closes, so that a game quit or crashed afterwards keeps it.
"""

from mods_base import HiddenOption

from . import history, report

# Never written yet: history.decode reads {} as no run.
option = HiddenOption("history", {})
_runs: dict[str, tuple] = {"runs": ()}


def load() -> None:
    """The runs the settings file kept. What the read left out goes in the log; the next write leaves it out too."""
    loaded = history.decode(option.value)
    _runs["runs"] = loaded.runs
    report.note("history_read", runs=len(loaded.runs), repaired=loaded.repaired, unreadable=loaded.unreadable)


def runs() -> tuple[history.Run, ...]:
    return _runs["runs"]


def add(run: history.Run) -> bool:
    """The run on top of the history, written at once; whether the file took it. A write that fails keeps the run in
    the history until the game closes, and says so in the log."""
    from . import mod

    _runs["runs"] = history.record(_runs["runs"], run)
    option.value = history.encode(_runs["runs"])
    try:
        mod.save_settings()
    except Exception as error:
        report.note("history_not_saved", error=type(error).__name__)
        return False
    return True
