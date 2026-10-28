"""Tests the starting points as the mod uses them (start_places.py): Kevin's seven places in his order, the setting's
choices their numbers, the first chosen at first; a number found, any other value read as the first place; each name
cut on two lines where the longer line is shortest, a name of one word kept whole."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import start_places  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("Kevin's seven places in his order", [place.number for place in start_places.PLACES] == [3, 5, 8, 9, 11, 12, 15])
check("the setting's choices are their numbers, the first chosen at first",
      start_places.NUMBERS == ("3", "5", "8", "9", "11", "12", "15") and start_places.DEFAULT == "3")
check("a number found, as text or as a number", start_places.find("11").name == "Pain Street"
      and start_places.find(15).name == "Locust Production Facility")
check("a place not kept, no value or another word read as the first place",
      all(start_places.find(value).number == 3 for value in ("10", None, "x", "", 3.5)))
check("each name on two lines where the longer line is shortest",
      [start_places.two_lines(place.name) for place in start_places.PLACES]
      == ["Purge\nGuard", "Checkpoint\nVermillion", "The Vestal\nGarrison", "The Deckled\nSprawl", "Pain\nStreet",
          "The\nGunkworks", "Locust Production\nFacility"])
check("a name of one word kept whole", start_places.two_lines("Crueltown") == "Crueltown")
check("fourteen pictures, each place's and its map's", len(start_places.PICTURES) == 14
      and start_places.PICTURES[-2:] == ("start_15_place.png", "start_15_map.png"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
