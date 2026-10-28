"""The mod's log lines: notes named after the mod; an error said once per key, then kept quiet; the keys bounded; a
reset lets an error be said again."""

import sys

import sdk_stubs

state = sdk_stubs.install()

from hunter_change import report  # noqa: E402

# Importing the mod turns it on, which says so: each check starts from an empty log.
state["logs"].clear()
state["errors"].clear()
report.reset()

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


report.note("enabled")
check("notes named after the mod", state["logs"] == ["[Hunter Change] enabled"])
report.error_once("look", "the look failed")
report.error_once("look", "the look failed again")
check("an error said once per key, then kept quiet", state["errors"] == ["[Hunter Change] the look failed"])
for index in range(report.MAX_ERRORS + 5):
    report.error_once(f"key{index}", "x")
check("the keys bounded", len(state["errors"]) == report.MAX_ERRORS)
report.reset()
report.error_once("look", "the look failed")
check("a reset lets an error be said again", state["errors"][-1] == "[Hunter Change] the look failed")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
