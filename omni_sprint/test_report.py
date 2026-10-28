"""Tests the log lines: signed with the mod's name, each failure and warning once, notes and keys bounded."""

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

from omni_sprint import report  # noqa: E402

report.note("hello")
check("a note is signed with the mod's name", state["misc"] == ["[Omni Sprint] hello"])
report.error_once("layout", "broken")
report.error_once("layout", "broken again")
check("each failure kind is written once", state["errors"] == ["[Omni Sprint] broken"])
report.warning_once("none:0x1", "not found")
report.warning_once("none:0x1", "not found")
check("each warning is written once", state["warnings"] == ["[Omni Sprint] not found"])
report.reset()
report.error_once("layout", "broken")
check("a switch-on starts afresh", len(state["errors"]) == 2)

report.MAX_NOTES = 3
report.reset()
for index in range(10):
    report.note(f"line {index}")
check("notes are bounded per switch-on", len(state["misc"]) == 1 + 3)

report.MAX_REPORTED = 2
report.reset()
for index in range(5):
    report.warning_once(f"key {index}", "w")
check("keys are bounded", len(state["warnings"]) == 1 + 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
