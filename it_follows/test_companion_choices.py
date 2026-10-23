"""Tests what the player chose on the COMPANIONS page (companion_choices.py): the team's names, those known, MOST at
most, in their order, nothing for a value that is no list; one more added, refused when full or unknown; one fewer
removed, the last one added; each companion's shield, speed and outfit read, the default for any part that is none; one
changed, the others kept and cleaned; each change a new value, the option's own never changed in place; the team's
choices as a team starts with them; the bars' option, off at first, under its name of 1.0.10."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import companion_choices as choices  # noqa: E402
from it_follows.characters.companions import kinds, pace  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("eight at most (decision 21); the speeds of the card, +20 % the trials' own", choices.MOST == 8
      and choices.SPEEDS == {"Off": 1.0, "+20%": pace.FACTOR, "+30%": 1.3} and choices.DEFAULT_SPEED == "+20%"
      and choices.Choice() == choices.Choice(True, "+20%", "own") and choices.Choice(False, "+30%").factor == 1.3)
check("the outfits: the hunter's own at first, the player's colours", choices.OUTFITS == ("own", "player"))
check("kept in two hidden options, empty at first", [option.identifier for option in choices.ALL] == [
      "companions_team", "companions_choices"] and choices.team.value == [] and choices.chosen.value == {})

check("the names known, in their order, the same one as often as chosen", choices.names(
      ["Vex", "Nobody", "Vex", 3, "Crankus"]) == ["Vex", "Vex", "Crankus"])
check("past MOST left out", choices.names(["Rafa"] * 12) == ["Rafa"] * 8)
check("a value that is no list: no team", choices.names("Vex") == [] and choices.names({"Vex": 1}) == [])

choices.team.value = held = ["Vex", "Rafa", "Vex"]
check("counted by name", choices.count("Vex") == 2 and choices.count("Amon") == 0)
check("one more: added at the end, a new list", choices.added("Amon") == ["Vex", "Rafa", "Vex", "Amon"]
      and choices.team.value is held and held == ["Vex", "Rafa", "Vex"])
check("an unknown name never added", choices.added("Nobody") is None)
choices.team.value = ["Vex"] * 8
check("full: the ninth refused", choices.added("Rafa") is None)
choices.team.value = held = ["Vex", "Rafa", "Vex", "Amon"]
check("one fewer: the last one added of that name", choices.removed("Vex") == ["Vex", "Rafa", "Amon"]
      and held == ["Vex", "Rafa", "Vex", "Amon"])
check("none of that name: the team as it is", choices.removed("Crankus") == ["Vex", "Rafa", "Vex", "Amon"])

check("nothing kept: the default", choices.choice("Vex") == choices.Choice())
choices.chosen.value = kept = {"Vex": {"shield": False, "speed": "+30%", "outfit": "player"},
                               "Rafa": {"shield": "no", "speed": "fast", "outfit": "gold"},
                               "Nobody": {"shield": False}, "Amon": "off"}
check("kept: read back", choices.choice("Vex") == choices.Choice(False, "+30%", "player"))
check("a part that is none: its default", choices.choice("Rafa") == choices.Choice()
      and choices.choice("Amon") == choices.Choice())
check("one changed, the others kept and cleaned, a new value", choices.changed("Rafa", speed="Off") == {
      "Vex": {"shield": False, "speed": "+30%", "outfit": "player"},
      "Rafa": {"shield": True, "speed": "Off", "outfit": "own"}, "Amon": {"shield": True, "speed": "+20%",
                                                                          "outfit": "own"}}
      and kept["Rafa"] == {"shield": "no", "speed": "fast", "outfit": "gold"})
check("its shield changed, its speed and outfit kept", choices.changed("Vex", shielded=True)["Vex"] == {
      "shield": True, "speed": "+30%", "outfit": "player"})
check("a speed that is none: its own kept", choices.changed("Vex", speed="+50%")["Vex"]["speed"] == "+30%")
check("its outfit changed, the rest kept", choices.changed("Vex", outfit="own")["Vex"] == {
      "shield": False, "speed": "+30%", "outfit": "own"})
check("an outfit that is none: its own kept", choices.changed("Vex", outfit="gold")["Vex"]["outfit"] == "player")
choices.chosen.value = {"Vex": {"speed": [], "outfit": {}}, "Rafa": {"speed": {"a": 1}, "outfit": ["own"]}}
check("a list or a table edited in by hand: its default, nothing raised (review of 22 October 2026)",
      choices.choice("Vex") == choices.Choice() and choices.choice("Rafa") == choices.Choice()
      and choices.changed("Vex", shielded=False)["Rafa"] == {"shield": True, "speed": "+20%", "outfit": "own"}
      and choices.team_choices() == {name: choices.Choice() for name in choices.names()})
choices.chosen.value = "broken"
check("a value that is no table: every choice its default, one changed alone", choices.choice("Vex")
      == choices.Choice() and choices.changed("Vex", shielded=False) == {"Vex": {"shield": False, "speed": "+20%",
                                                                                 "outfit": "own"}})

choices.team.value = ["Vex", "Crankus", "Vex"]
choices.chosen.value = {"Vex": {"shield": False, "speed": "Off"}}
check("the team's choices, one per name", choices.team_choices() == {"Vex": choices.Choice(False, "Off"),
                                                                     "Crankus": choices.Choice()})
check("every name the card offers is a companion", all(name in kinds.BY_NAME for name in ("Vex", "Crankus")))
check("the bars' option off at first, under the name the settings of 1.0.10 keep", choices.bars.identifier
      == "companion_bars" and choices.bars.value is False and choices.MOST == kinds.MOST)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
