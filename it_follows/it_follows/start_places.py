"""The Horde's starting points as the mod uses them (docs/RUN/spec-points-de-depart.md): the place a setting names, and
its name on two lines for its tab (Kevin, decision 140: « il les faut sur deux ligne comme dans A »). The places are
start_places_data.py's, made by docs/RUN/outils/start_points_build.py from Kevin's marks."""

from .start_places_data import PICTURES, PLACES, Place

# The starting place setting's choices, its numbers as text, in the tabs' order; the first is chosen at first.
NUMBERS = tuple(str(place.number) for place in PLACES)
DEFAULT = NUMBERS[0]

__all__ = ["DEFAULT", "NUMBERS", "PICTURES", "PLACES", "Place", "find", "two_lines"]


def find(value: object) -> Place:
    """The place a setting names, the first for any value that names none: a settings file edited by hand never keeps
    a run from starting."""
    return next((place for place in PLACES if str(place.number) == str(value)), PLACES[0])


def two_lines(name: str) -> str:
    """The name on two lines, cut at the space that leaves the longer line shortest, the first such space."""
    words = name.split(" ")
    if len(words) < 2:
        return name
    cut = min(range(1, len(words)), key=lambda at: max(len(" ".join(words[:at])), len(" ".join(words[at:]))))
    return " ".join(words[:cut]) + "\n" + " ".join(words[cut:])
