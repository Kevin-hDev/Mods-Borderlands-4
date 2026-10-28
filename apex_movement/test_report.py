"""Tests the log lines: signed with the name of the file that wrote them, each failure kind written once, bounded."""

import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import pack, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


report.note("sprint request on")
check("a line is signed with the file's own name", state["misc"][-1] == f"[{pack.NAME}] sprint request on")
check("which is the pack's name in the full pack", pack.NAME == "Apex Movement")

# A separate file, as the build tool writes its pack.py: two files installed together must not sign alike (review,
# 2026-09-18: every line said [Apex Movement], whichever file wrote it).
pack.NAME = "Apex Dash"
importlib.reload(report)
report.note("dash distance on")
check("a separate file signs its lines with its own name", state["misc"][-1] == "[Apex Dash] dash distance on")
pack.NAME = "Apex Movement"
importlib.reload(report)

report.warning("careful")
check("a warning is signed too", state["warnings"][-1] == f"[{pack.NAME}] careful")

report.error_once("slide_asset", "Move_Slide not found")
report.error_once("slide_asset", "Move_Slide not found")
check("a failure kind is written once", len(state["errors"]) == 1)
report.error_once("dash_asset", "Move_Dash not found")
check("another kind is written too", len(state["errors"]) == 2)

for kind in range(report.MAX_REPORTED + 50):
    report.error_once(f"kind {kind}", "boom")
check("the kinds kept are bounded", len(report._reported) == report.MAX_REPORTED)

report.reset()
report.error_once("slide_asset", "Move_Slide not found")
check("after a reset a kind is written again", state["errors"][-1].endswith("Move_Slide not found"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
