"""Tests a mod's log lines (characters/report.py): one JSON line an event, with the run's number; a field that would
replace event or run refused; a call written before it is made unless it is one made at every sample; a sentence cut
to its limit; a line cut to its limit; behind a neutral name until the mod carrying the package names it, a name that
is no mod's refused and the one kept."""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from characters import report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def last() -> dict:
    line = state["info"][-1]
    return json.loads(line.removeprefix(report.PREFIX + " "))


try:
    report.note("idle", level=40)
    check("before any run, a line carries run 0", last() == {"event": "idle", "run": 0, "level": 40}
          and state["info"][-1].startswith("[Characters] {"))
    check("each run has the next number", report.begin_run() == 1 and report.begin_run() == 2)
    report.note("started", horde=12)
    check("a line carries the run it belongs to", last() == {"event": "started", "run": 2, "horde": 12})
    for name in ("event", "run"):
        try:
            report.note("x", **{name: 1})
            refused = False
        except TypeError:
            refused = True
        check(f"a field named {name} is refused", refused)
    count = len(state["info"])
    report.announce("SetTerritory", on="Char_Cat_1")
    check("a risky call is written before it is made",
          last() == {"event": "call", "run": 2, "call": "SetTerritory", "on": "Char_Cat_1"})
    report.announce("K2_TeleportTo", log=False, on="Char_Cat_1")
    check("a call made at every sample is not written", len(state["info"]) == count + 1)
    report.note("odd", value=object())
    check("a value JSON cannot hold is written as text", last()["value"].startswith("<object object"))
    report.note("long", words="x" * 10_000)
    check("a line is cut to its limit", len(state["info"][-1]) == len(report.PREFIX) + 1 + report.MAX_LINE)
    report.said("y" * 1000)
    check("a sentence is cut to its limit", state["info"][-1] == report.PREFIX + " " + "y" * report.MAX_TEXT)
    check("a neutral name until a mod names its copy", report.PREFIX == "[Characters]")
    report.named("Companions")
    report.note("named")
    check("named by its mod: its lines behind that name", report.PREFIX == "[Companions]"
          and state["info"][-1].startswith('[Companions] {"event":"named"'))
    for wrong in ("", "x" * 41, "It Follows]\n[Other", "../mods", 3, None):
        try:
            report.named(wrong)
            refused = False
        except ValueError:
            refused = True
        check(f"a name that is no mod's refused, the one there kept: {wrong!r}", refused
              and report.PREFIX == "[Companions]")
    report.named("It Follows")
    check("It Follows' name, a space in it", report.PREFIX == "[It Follows]")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
