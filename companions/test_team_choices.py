"""Tests what the player chose on the cards (team_choices.py): the team by the characters' package's rules (a name
unknown left out, MOST at most, a ninth refused, the last one taken away), each change a new value; a hunter's outfit,
his own at first and for anything that is none; one changed, the other hunters' kept and cleaned, an ally or an outfit
unknown changing nothing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from companions import settings, team_choices as choices  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("eight at most; the outfits his own, then the player's colours", choices.MOST == 8
      and choices.OUTFITS == ("own", "player"))
check("no team at first", choices.names() == [])
settings.team.value = ["Vex", "Nobody", "Vex", 3, "Crankus"]
check("the names known, in their order", choices.names() == ["Vex", "Vex", "Crankus"])
held = settings.team.value
check("one more: a new list, the held one untouched", choices.added("Amon") == ["Vex", "Vex", "Crankus", "Amon"]
      and settings.team.value is held and held == ["Vex", "Nobody", "Vex", 3, "Crankus"])
settings.team.value = ["Rafa"] * 8
check("a ninth refused", choices.added("Vex") is None)
settings.team.value = ["Vex", "Rafa", "Vex"]
check("one fewer: the last one of that name", choices.removed("Vex") == ["Vex", "Rafa"])
settings.team.value = []

check("an outfit at first: his own", choices.outfit("Vex") == "own")
settings.outfits.value = {"Vex": "player", "Rafa": "gold", "Amon": 3}
check("one kept: read; one that is none: his own", choices.outfit("Vex") == "player"
      and choices.outfit("Rafa") == "own" and choices.outfit("Amon") == "own")
settings.outfits.value = "player"
check("a value that is no dict: his own", choices.outfit("Vex") == "own")
settings.outfits.value = {"Vex": "player", "Rafa": "gold", "Crankus": "player", "Nobody": "player"}
held = settings.outfits.value
check("one changed: the other hunters' kept and cleaned, an ally and a name unknown left out",
      choices.with_outfit("Amon", "player") == {"Vex": "player", "Rafa": "own", "Amon": "player"}
      and settings.outfits.value is held)
check("an ally or an outfit unknown: nothing changed", choices.with_outfit("Crankus", "player") == {
      "Vex": "player", "Rafa": "own"} and choices.with_outfit("Vex", "gold") == {"Vex": "player", "Rafa": "own"})
check("given a value to read: that one", choices.outfit("Vex", {"Vex": "own"}) == "own")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
