"""Tests the log lines: signed with the mod's name, each failure once, notes bounded."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from vehicle_driving import report  # noqa: E402

report.note("hello")
check("a note is signed with the mod's name", state["misc"] == ["[Vehicle Driving] hello"])
report.error_once("grip", "broken")
report.error_once("grip", "broken again")
check("each failure kind is written once", state["errors"] == ["[Vehicle Driving] broken"])
report.reset()
report.error_once("grip", "broken")
check("after a reset it is written again", len(state["errors"]) == 2)
for _ in range(report.MAX_NOTES + 10):
    report.note("x")
check("notes are bounded, so a long drive cannot fill the log", len(state["misc"]) == 1 + report.MAX_NOTES)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
