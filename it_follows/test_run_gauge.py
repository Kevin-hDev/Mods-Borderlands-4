"""Tests what a run measures of itself (run_gauge.py): the longest second and each task's longest kept until the status
line, then counted afresh; a second or a task longer than SLOW_S written at once with the horde's size; the status
line due every STATUS_EVERY_S, the first that long after the start; the images a second over the line's span and its
lowest second, from the engine's image count, a span longer than LONGEST_SPAN_S or after an unread count left out."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import run_gauge  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    lines: list[tuple[str, dict]] = []
    gauge = run_gauge.Gauge(lambda event, **fields: lines.append((event, fields)), 100.0)
    check("no status line before STATUS_EVERY_S", not gauge.status_due(129.9))
    gauge.second(30.0, 50)
    gauge.second(80.04, 120)
    gauge.task("census", 21.26, 120)
    gauge.task("census", 17.0, 120)
    gauge.task("game_camps", 13.0, 120)
    check("seconds and tasks under SLOW_S write nothing at once", lines == [])
    check("the status line due at STATUS_EVERY_S, the next that long after",
          gauge.status_due(130.0) and not gauge.status_due(159.0) and gauge.status_due(160.0))
    check("the longest second and each task's longest, rounded",
          gauge.spent() == {"slowest_ms": 80.0, "tasks_ms": {"census": 21.3, "game_camps": 13.0}, "fps": None,
                            "fps_low": None})
    check("then counted afresh", gauge.spent() == {"slowest_ms": 0.0, "tasks_ms": {}, "fps": None,
                                                   "fps_low": None})
    gauge.frames(None, 199.0)
    gauge.frames(1000, 200.0)
    check("a first count only starts the span", gauge.images == 0 and gauge.counted == (1000, 200.0))
    gauge.frames(1060, 201.0)
    gauge.frames(1110, 202.0)
    gauge.frames(1400, 210.0)
    gauge.frames(1460, 211.0)
    gauge.frames(None, 212.0)
    gauge.frames(1520, 213.0)
    check("the images a second over the counted spans and the lowest second; a pause and an unread count left out",
          gauge.spent() == {"slowest_ms": 0.0, "tasks_ms": {}, "fps": 56.7, "fps_low": 50.0})
    gauge.frames(1580, 214.0)
    check("then counted afresh from the last count", gauge.spent()["fps"] == 60.0 and gauge.spent()["fps"] is None)
    gauge.frames(1500, 215.0)
    check("a count going back is left out", gauge.spent()["fps"] is None and gauge.counted == (1500, 215.0))
    gauge.second(612.34, 90)
    gauge.task("follow", 501.0, 90)
    check("a second or a task longer than SLOW_S written at once, with the horde's size",
          lines == [("slow_sample", {"took_ms": 612.3, "horde": 90}),
                    ("slow_task", {"task": "follow", "took_ms": 501.0, "horde": 90})])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
