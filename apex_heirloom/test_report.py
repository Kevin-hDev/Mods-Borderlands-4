"""Tests the log lines: signed with the mod's name, each failure once, notes and failure kinds bounded."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()

from apex_heirloom import report  # noqa: E402

report.note("hello")
check("a note is signed with the mod's name", state["misc"] == ["[Tidy Weapons] hello"])
report.error_once("put_away", "broken")
report.error_once("put_away", "broken again")
check("each failure kind is written once", state["errors"] == ["[Tidy Weapons] broken"])
report.reset()
report.error_once("put_away", "broken")
check("a switch-on starts afresh", len(state["errors"]) == 2)

report.MAX_NOTES = 3
report.reset()
for index in range(10):
    report.note(f"line {index}")
check("notes are bounded per switch-on", len(state["misc"]) == 1 + 3)

report.MAX_REPORTED = 2
report.reset()
for index in range(5):
    report.error_once(f"key {index}", "e")
check("failure kinds are bounded", len(state["errors"]) == 2 + 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
