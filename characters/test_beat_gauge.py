"""Tests what a beat measures of itself: its hook's calls a second and the µs a call with nothing to do took, then
counted afresh, None without such a call; the images a second over the line's span and its lowest second, from the
engine's image count, a span longer than LONGEST_SPAN_S, a count going back or after an unread count left out, then
counted afresh from the last count."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from characters import beat_gauge  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    clock = [300.0]
    precise = [0.0]

    def two_us() -> float:
        precise[0] += 0.000002
        return precise[0]

    beat_gauge.perf_counter = two_us
    calls = beat_gauge.Calls(lambda: clock[0])
    for step in range(90):
        began = calls.called()
        if step % 3:
            calls.idle(began)
    clock[0] = 300.9
    said = calls.said()
    check("the calls a second, and the µs a call with nothing to do took",
          said == {"hook_calls_s": 100.0, "hook_idle_us": 2.0})
    check("then counted afresh", calls.calls == 0 and calls.idle_calls == 0 and calls.idle_s == 0.0
          and calls.counted_at == 300.9)
    calls.called()
    clock[0] = 301.9
    check("no call with nothing to do: no µs", calls.said() == {"hook_calls_s": 1.0, "hook_idle_us": None})
    check("no time spent: no calls a second", calls.said()["hook_calls_s"] == 0.0)

    rate = beat_gauge.FrameRate()
    rate.read(None, 199.0)
    rate.read(1000, 200.0)
    check("a first count only starts the span", rate.images == 0 and rate.counted == (1000, 200.0))
    rate.read(1060, 201.0)
    rate.read(1110, 202.0)
    rate.read(1400, 210.0)
    rate.read(1460, 211.0)
    rate.read(None, 212.0)
    rate.read(1520, 213.0)
    check("the images a second over the counted spans and the lowest second; a pause and an unread count left out",
          rate.said() == {"fps": 56.7, "fps_low": 50.0})
    rate.read(1580, 214.0)
    check("then counted afresh from the last count", rate.said()["fps"] == 60.0 and rate.said()["fps"] is None)
    rate.read(1500, 215.0)
    check("a count going back is left out", rate.said() == {"fps": None, "fps_low": None}
          and rate.counted == (1500, 215.0))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
