"""Whether the game shows its main menu, for the team to stop there (decision 61 of docs/renforts, Kevin,
22 October 2026: « Arrêt à chaque menu »). The menu and a game share the map World_P, so its name tells nothing; the
menu's station (MainMenuStationObject, one in World_P) is shown on the title screen and the hunters' list and hidden
in a game (docs/reverse-and-change-hunters, 27 September 2026, source unique until trial 206). Read only.

Why the last read told nothing is kept (why), for the team's journal: trial 212 read nothing from 09:45:17 to its
end, and the journal could not say why (review of 23 October 2026)."""

from typing import Any, Callable, Iterable

CLASS = "MainMenuStationObject"
MAX_TEXT = 80
_last = {"why": ""}


def why() -> str:
    """Why the last read told nothing: no_controller, no_station, or the error that broke it; empty after a read."""
    return _last["why"]


def showing(pc: Any, search: Callable[[str, Any], tuple[Iterable[Any], str]] | None = None) -> bool | None:
    """True when the menu's station shows, False when it is hidden; None when it cannot be read (no controller, no
    station found, a read failing): the team then goes on, as before. search(class, actor) is It Follows'
    reads.search, 0.03 to 0.06 ms an asking with the controller (trial 38)."""
    if pc is None:
        _last["why"] = "no_controller"
        return None
    if search is None:
        from ..reads import search
    try:
        found, _way = search(CLASS, pc)
        # find_all, should the actors' search fail, also gives the class default, never in the world.
        station = next((one for one in found if not str(one.Name).startswith("Default__")), None)
        _last["why"] = "no_station" if station is None else ""
        return None if station is None else not bool(station.bHidden)
    except Exception as error:
        _last["why"] = f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}"
        return None
