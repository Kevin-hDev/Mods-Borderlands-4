"""START with a starting point (decision 138, spec-points-de-depart.md, section 4): the player sent there first
(start_trip.py), the run started once the trip is over and the player can play, with the settings of START. session.py
asks for it after its own refusals and gives what makes the run; this module never touches the window.

A trip that ends badly, or a run that does not start at its end, keeps its reason for the window and calls the
window's on_failed, which opens it again to say it (as BL4 Arena's window does after a trip that failed); a trip
cancelled, the mod switched off, says nothing. A run refused on arrival keeps ARRIVAL_COOP or ARRIVAL_REFUSED, not
START's own reasons: those say the game is not changed, and the player has been moved (It Follows' audit,
2026-10-19)."""

from typing import Any, Callable

import mods_base

from . import presence, report, start_places, start_trip

# START's answer while the player is on his way to the starting point.
TRAVELLING = "travelling"
# Why the run did not start on arrival: a friend joined on the way, or anything else.
ARRIVAL_COOP, ARRIVAL_REFUSED = "arrival_coop", "arrival_refused"
# Why the last trip did not end in a run, until the window reads it.
_state: dict = {"outcome": None}

Begin = Callable[[Any, Any, Any, "int | None"], str]


def go(settings: Any, pc: Any, player: Any, on_failed: Callable[[], None] | None, begin: Begin,
       busy: Callable[[], str]) -> str:
    """The trip to the place settings name: TRAVELLING, or why nothing moved. begin(settings, pc, player, players)
    makes and begins the run; busy() says why a run cannot start now, "" when it can."""
    place = start_places.find(settings.start_place)
    _state["outcome"] = None
    why = start_trip.go(place, pc, player, lambda: _arrived(settings, on_failed, begin, busy),
                        lambda outcome: _failed(outcome, on_failed))
    report.note("start_trip_asked", place=place.number, outcome=why or TRAVELLING)
    return why or TRAVELLING


def _arrived(settings: Any, on_failed: Callable[[], None] | None, begin: Begin, busy: Callable[[], str]) -> None:
    """The trip over, the player able to play where it set him: the run starts there."""
    pc = mods_base.get_pc()
    player = getattr(pc, "OakCharacter", None) if pc is not None else None
    outcome = busy() or ("no_character" if player is None else begin(settings, pc, player, presence.players()))
    report.note("start_arrived", outcome=outcome)
    if outcome != "started":
        _failed(ARRIVAL_COOP if outcome == "coop" else ARRIVAL_REFUSED, on_failed)


def _failed(outcome: str, on_failed: Callable[[], None] | None) -> None:
    report.note("start_trip_failed", outcome=outcome)
    if outcome == start_trip.CANCELLED:
        return
    _state["outcome"] = outcome
    report.said("No run started at the starting point. Press START to try again; the reason is in unrealsdk.log.")
    if on_failed is None:
        return
    try:
        on_failed()
    except Exception as error:
        report.note("start_reopen_failed", error=type(error).__name__)


def take_outcome() -> str | None:
    """Why the last trip did not end in a run, once: the window says it, then it is gone."""
    outcome, _state["outcome"] = _state["outcome"], None
    return outcome


def travelling() -> bool:
    return start_trip.travelling()


def cancel(why: str) -> None:
    start_trip.cancel(why)
