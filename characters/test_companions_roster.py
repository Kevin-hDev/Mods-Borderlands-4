"""Tests the team a player makes (companions/roster.py): the names known, in their order, the same one as often as
chosen, past MOST left out, nothing for a value that is no list; one more added, refused when full or unknown, a new
list each time; one fewer removed, the last one added, the team as it is when there is none."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from characters.companions import kinds, roster  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("eight at most, the team's own", roster.MOST == kinds.MOST == 8)
check("the names known, in their order, the same one as often as chosen", roster.names(
      ["Vex", "Nobody", "Vex", 3, "Crankus"]) == ["Vex", "Vex", "Crankus"])
check("past MOST left out", roster.names(["Rafa"] * 12) == ["Rafa"] * 8)


class Counted(list):
    """A list that counts the names read from it."""
    read = 0

    def __iter__(self):
        for name in list.__iter__(self):
            Counted.read += 1
            yield name


check("a list edited by hand, however long: read only up to its MOST-th known name (review of 23 October 2026)",
      roster.names(Counted(["Nobody", *["Rafa"] * 10000])) == ["Rafa"] * 8 and Counted.read == 9)
Counted.read = 0
check("a list of names it does not know: read READ_MOST entries at most, no team",
      roster.names(Counted(["Nobody"] * 10000 + ["Rafa"])) == [] and Counted.read == roster.READ_MOST)
check("a value that is no list: no team", roster.names("Vex") == [] and roster.names({"Vex": 1}) == []
      and roster.names(None) == [])
held = ["Vex"]
grown = roster.added(held, "Crankus")
check("one more added, at the end, a new list", grown == ["Vex", "Crankus"] and held == ["Vex"] and grown is not held)
check("an unknown name refused", roster.added(held, "Nobody") is None)
check("a full team refuses a ninth", roster.added(["Rafa"] * 8, "Vex") is None
      and roster.added(["Rafa"] * 7, "Vex") == ["Rafa"] * 7 + ["Vex"])
check("one fewer: the last one of that name added", roster.removed(["Vex", "Rafa", "Vex", "Amon"], "Vex") == [
      "Vex", "Rafa", "Amon"])
check("none of that name: the team as it is", roster.removed(["Vex"], "Rafa") == ["Vex"])
check("a value that is no list: removing gives no team", roster.removed("Vex", "Vex") == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
