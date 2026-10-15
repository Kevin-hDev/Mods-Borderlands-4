"""Tests what follows a run's end (ending.py) and the history it is kept in (kept.py): the history read when the mod
starts, what it left out written in the log; a run ended by STOP kept on top with its moment, level, limit, time and
counts, written at once, its result waiting; at the end of its time the window opened on it, a window that cannot open
said in the log, and never opened while the player drives; a run that stopped by itself waiting too; one ended by
leaving the game or turning the mod off kept with no result; a write that fails keeps the run until the game closes,
and says so."""

import json
import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import it_follows  # noqa: E402
from it_follows import control_window, ending, history, kept, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def last(event: str) -> dict:
    found = [json.loads(line[len(report.PREFIX) + 1:]) for line in state["info"]
             if line.startswith(report.PREFIX + " {") and f'"event":"{event}"' in line]
    return found[-1] if found else {}


def finished(limit: float | None = 600.0, played: float = 125.8) -> SimpleNamespace:
    return SimpleNamespace(settings=SimpleNamespace(duration_s=limit), level=SimpleNamespace(target=60),
                           clock=SimpleNamespace(played=played), stats=SimpleNamespace(kills=33, deaths=1))


opened: list = []
control_window.start = lambda: opened.append(True)

try:
    kept.option.value = {"version": 1, "runs": [{"when": 5, "level": 40, "limit_s": None, "played_s": 9, "kills": 1,
                                                 "deaths": 0, "end": "stopped"}, {"broken": True}]}
    kept.load()
    check("the history read when the mod starts, what it left out written in the log",
          [run.when for run in kept.runs()] == [5] and last("history_read") == {
              "event": "history_read", "run": 0, "runs": 1, "repaired": 1, "unreadable": ""})
    saves = it_follows.mod.saves
    it_follows.mod.save_settings = lambda: setattr(it_follows.mod, "saves", it_follows.mod.saves + 1)
    done = ending.ended(finished(), 1_760_000_000, "stopped")
    check("a run ended by STOP kept on top, with its moment, level, limit, time and counts, written at once",
          kept.runs()[0] == done == history.Run(1_760_000_000, 60, 600, 125, 33, 1, "stopped")
          and it_follows.mod.saves == saves + 1 and kept.option.value == history.encode(kept.runs())
          and last("history_added") == {"event": "history_added", "run": 0, "saved": True, "end": "stopped"})
    check("its result waiting, no window opened by itself", ending.waiting() is done and opened == [])
    ending.shown()
    check("shown once, it waits no more", ending.waiting() is None)
    state["pc"] = SimpleNamespace(OakCharacter=object(), Pawn=None)
    done = ending.ended(finished(), 1_760_000_100, "time_up")
    check("at the end of its time, the window opened on its result", opened == [True] and ending.waiting() is done
          and done.end == "time_up")
    ending.shown()
    state["pc"] = SimpleNamespace(OakCharacter=None, Pawn=SimpleNamespace(Class=SimpleNamespace(Name="OakVehicle_C")))
    done = ending.ended(finished(), 1_760_000_150, "time_up")
    check("its time up while the player drives: no window opened, said, the result waiting for F5",
          opened == [True] and ending.waiting() is done
          and last("result_window_waits") == {"event": "result_window_waits", "run": 0, "why": "in_vehicle"})
    state["pc"] = SimpleNamespace(OakCharacter=object(), Pawn=None)

    def refused() -> None:
        raise RuntimeError("no window")

    control_window.start = refused
    ending.ended(finished(), 1_760_000_200, "time_up")
    check("a window that cannot open: said in the log, the result waiting for the next opening",
          last("result_window_failed") == {"event": "result_window_failed", "run": 0, "error": "RuntimeError"}
          and ending.waiting().when == 1_760_000_200)
    ending.shown()
    done = ending.ended(finished(limit=None), 1_760_000_300, "zone_lost")
    check("a run that stopped by itself: named so, its result waiting", done.end == "interrupted"
          and done.limit_s is None and ending.waiting() is done)
    ending.shown()
    for reason in ("left_game", "mod_disabled"):
        done = ending.ended(finished(), 1_760_000_400, reason)
        check(f"{reason}: kept, no result", kept.runs()[0] is done and done.end == reason and ending.waiting() is None)

    def broken() -> None:
        raise OSError("disk full")

    it_follows.mod.save_settings = broken
    done = ending.ended(finished(), 1_760_000_500, "stopped")
    check("a write that fails: the run kept until the game closes, said in the log", kept.runs()[0] is done
          and last("history_not_saved") == {"event": "history_not_saved", "run": 0, "error": "OSError"}
          and last("history_added")["saved"] is False)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
