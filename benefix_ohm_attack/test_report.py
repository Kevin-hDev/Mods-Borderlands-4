"""Tests the mod's lines in the SDK log: what it does as it happens, each failure once, a bounded memory."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


report.note("beam on")
report.note("beam on")
check("what the mod does is written each time, under its name",
      state["log"] == ["[Benefix Ohm Attack] beam on"] * 2 and state["errors"] == [])
report.error_once("hand", "the hand could not be read")
report.error_once("hand", "the hand could not be read, again")
report.error_once("beam", "the beam could not be lit")
check("a failure is written as an error, once per kind",
      state["errors"] == ["[Benefix Ohm Attack] the hand could not be read", "[Benefix Ohm Attack] the beam could not be lit"])
report.reset()
report.error_once("hand", "the hand could not be read")
check("after a reset a kind already said is said again", len(state["errors"]) == 3)

report.reset()
said = len(state["errors"])
for number in range(report.MAX_REPORTED + 50):
    report.error_once(f"kind {number}", "one more kind of failure")
check("the kinds remembered are bounded: past the bound, new kinds are dropped",
      report.MAX_REPORTED == 100 and len(state["errors"]) == said + report.MAX_REPORTED)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
