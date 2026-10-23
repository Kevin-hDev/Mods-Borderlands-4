"""Whether the game shows its main menu, for the team to stop there (decision 61 of docs/renforts, Kevin,
22 October 2026: « Arrêt à chaque menu »). The menu and a game share the map World_P, so its name tells nothing; the
menu's station (MainMenuStationObject, one in World_P) is shown on the title screen and the hunters' list and hidden
in a game (docs/reverse-and-change-hunters, 27 September 2026, source unique until trial 206). Read only."""

from typing import Any, Callable, Iterable

CLASS = "MainMenuStationObject"


def showing(pc: Any, search: Callable[[str, Any], tuple[Iterable[Any], str]] | None = None) -> bool | None:
    """True when the menu's station shows, False when it is hidden; None when it cannot be read (no controller, no
    station found, a read failing): the team then goes on, as before. search(class, actor) is It Follows'
    reads.search, 0.03 to 0.06 ms an asking with the controller (trial 38)."""
    if pc is None:
        return None
    if search is None:
        from ..reads import search
    try:
        found, _way = search(CLASS, pc)
        # find_all, should the actors' search fail, also gives the class default, never in the world.
        station = next((one for one in found if not str(one.Name).startswith("Default__")), None)
        return None if station is None else not bool(station.bHidden)
    except Exception:
        return None
