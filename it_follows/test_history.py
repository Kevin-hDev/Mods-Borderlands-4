"""Tests the last runs' layout: a run goes on top, the oldest past 20 dropped; a stop's reason named as the history
names it; the layout carries its version; read back as written; a value never written read as no run; a malformed run
left out and counted, a value that is no mapping set aside with why, a list that is no list counted, a later version's
unknown fields ignored, past 20 cut."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import history  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def run(when: int, **changed: object) -> history.Run:
    fields = {"when": when, "level": 40, "limit_s": 1800, "played_s": 1800, "kills": 412, "deaths": 2,
              "end": "time_up"}
    fields.update(changed)
    return history.Run(**fields)


try:
    runs: tuple = ()
    for when in range(25):
        runs = history.record(runs, run(1_760_000_000 + when))
    check("a run goes on top, the oldest past 20 dropped", len(runs) == history.MAX_RUNS == 20
          and runs[0].when == 1_760_000_024 and runs[-1].when == 1_760_000_005)
    check("a stop's reason named as the history names it", [history.end_of(reason) for reason in (
        "time_up", "stopped", "left_game", "mod_disabled", "zone_lost", "error:KeyError")]
        == ["time_up", "stopped", "left_game", "mod_disabled", "interrupted", "interrupted"])
    written = history.encode(runs[:2] + (run(5, limit_s=None, end="stopped"),))
    check("the layout carries its version", written["version"] == history.VERSION == 1)
    check("read back as written", history.decode(written) == history.Loaded(runs[:2] + (run(5, limit_s=None,
                                                                                            end="stopped"),)))
    check("a value never written reads as no run", history.decode({}) == history.Loaded(()))
    broken = {"version": 1, "runs": [run(1)._asdict(), {"when": "today"}, run(2, end="exploded")._asdict(),
                                     run(3, kills=-1)._asdict(), run(4, level=True)._asdict(), 7,
                                     {**run(6)._asdict(), "weather": "rain"}]}
    check("a malformed run left out and counted, a later version's unknown fields ignored",
          history.decode(broken) == history.Loaded((run(1), run(6)), repaired=5))
    check("a value that is no mapping set aside, with why", history.decode([1, 2]).unreadable
          == "not a mapping (list)" and history.decode([1, 2]).runs == ())
    check("runs that are no list counted", history.decode({"runs": "many"}) == history.Loaded((), repaired=1))
    check("past 20, cut", len(history.decode({"runs": [run(when)._asdict() for when in range(30)]}).runs) == 20)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
