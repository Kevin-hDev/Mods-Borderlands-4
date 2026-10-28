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

report.reset()
for _ in range(report.MAX_SUMMARIES + 10):
    report.note(report.Summary("grip frames=4 largest_turn=36.0"))
count = len(state["misc"])
report.note("driving OakVehicle_1")
check("summaries have their own bound: once they are spent, what happens still reaches the log",
      count == 1 + report.MAX_NOTES + report.MAX_SUMMARIES
      and state["misc"][-1] == "[Vehicle Driving] driving OakVehicle_1")
report.reset()
report.note(report.Summary("grip frames=4 largest_turn=36.0"))
check("a reset gives the summaries their room back", len(state["misc"]) == count + 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
