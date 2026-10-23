"""Tests Companions' journal (companions/report.py): the characters' package's journal in its place, named
Companions, one module for Companions' modules, its window's and the package's (decision 69 of docs/renforts): one run
number, one set of the window's errors."""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from companions import report  # noqa: E402
from companions.characters import report as shared  # noqa: E402
from companions.characters.companions import team  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("Companions' journal is the package's, one module", report is shared
      and sys.modules["companions.report"] is shared)
check("named Companions", report.PREFIX == "[Companions]")
number = report.begin_run()
team.report.note("from_the_companions")
line = state["info"][-1]
check("a line of the companions' code behind Companions' name, in its run", line.startswith("[Companions] {")
      and json.loads(line.removeprefix("[Companions] ")) == {"event": "from_the_companions", "run": number})
report.error_once("window", "once")
shared.error_once("window", "twice")
check("one set of the window's errors written once", len(state["errors"]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
