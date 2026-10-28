"""The HUNTER page's state, apart from its widgets (conception-idee-2.md, « Ce que le joueur voit »): where the window
is, the hunter of the game there as its save says, and what a click does. In a game, a click asks for a confirmation,
then leave.py takes the player back to the main menu; at the title screen, a click changes the selected game at once
(switch.py). Where no change can be made the page shows no card, only why (Kevin's rule, working or invisible).

The save is read when the place changes, never at each poll of the window: finding and opening it takes about 0.1 s
(essai 37), during which the game waits.
"""

from dataclasses import dataclass
from pathlib import Path

from mods_base import get_pc

from . import hunters, leave, report, save_places, save_text, switch, trees
from .game_id import game_id
from .hunters import Hunter

NOWHERE, UNAVAILABLE, BUSY, CARDS, CONFIRM = "nowhere", "unavailable", "busy", "cards", "confirm"


@dataclass(frozen=True)
class View:
    kind: str
    in_game: bool = False
    current: Hunter | None = None
    wanted: Hunter | None = None
    kept: bool = False
    why: str | None = None
    said: switch.Outcome | None = None
    said_to: Hunter | None = None


def _place() -> tuple[str, str, Hunter | None] | None:
    """("game", id, hunter played) in a game, ("title", id, None) at the title screen with a game selected, else None."""
    pc = get_pc()
    player_state = getattr(pc, "PlayerState", None) if pc is not None else None
    game = game_id(player_state)
    if game is None:
        return None
    if getattr(pc, "OakCharacter", None) is None:
        return "title", game, None
    return "game", game, hunters.played(player_state)


class SwitchPage:
    def __init__(self, places: list[Path] | None = None) -> None:
        self.places = places
        self.where, self.busy = _place(), leave.busy()
        self.view = self._read()

    def follow(self) -> bool:
        """Follows the game while the window is open; True when the view changed."""
        where, busy = _place(), leave.busy()
        if where == self.where and busy == self.busy:
            return False
        self.where, self.busy = where, busy
        before, self.view = self.view, self._read()
        return self.view != before

    def _moved(self) -> bool:
        """Whether the place or the request changed since the last poll, the view then following them: a click must
        not act on a game the player no longer sees, which switch.change does not check. No save read when nothing
        changed."""
        if (_place(), leave.busy()) == (self.where, self.busy):
            return False
        self.follow()
        return True

    def _read(self, said: switch.Outcome | None = None, said_to: Hunter | None = None) -> View:
        if self.where is None:
            return View(NOWHERE)
        kind, game, played = self.where
        in_game = kind == "game"
        if self.busy:
            return View(BUSY, in_game)
        # Taken before the checks, so that an end is said with no card too, where it matters most; in the game too,
        # where a request can end before reaching the title screen (no_return, gave_up).
        ended = leave.take_last(game) if said is None else None
        if ended is not None:
            said, said_to = ended.outcome, hunters.by_code(ended.wanted)
        trees.forget()
        if not trees.readable():
            return View(UNAVAILABLE, in_game, why="trees_unreadable", said=said, said_to=said_to)
        save = save_places.find(game, self.places)
        if (isinstance(save, save_places.Save) and ended is not None and ended.stamp is not None
                and ended.stamp != save_places.stamp(save)):
            # The game wrote the save since the end (whole-branch review, 2026-09-29): its next step was followed or
            # overtaken, maybe hours ago, and saying it now would ask the player to do it again. Taken all the same.
            said, said_to = None, None
        if isinstance(save, save_places.Missing):
            return View(UNAVAILABLE, in_game, why=save.why, said=said, said_to=said_to)
        head = save_text.header(save.text)
        current = hunters.by_character(head["hunter"]) if head is not None else None
        if current is None:
            return View(UNAVAILABLE, in_game, why="unknown_hunter", said=said, said_to=said_to)
        if in_game and current != played:
            return View(UNAVAILABLE, in_game, why="not_this_hunter", said=said, said_to=said_to)
        return View(CARDS, in_game, current, said=said, said_to=said_to)

    def click(self, code: str) -> None:
        if self._moved():
            return
        wanted, view = hunters.by_code(code), self.view
        if view.kind != CARDS or wanted is None or wanted == view.current:
            return
        _, game, _ = self.where
        if view.in_game:
            self.view = View(CONFIRM, True, view.current, wanted, kept=trees.kept(game, wanted.code) is not None)
            return
        try:
            outcome = switch.change(game, view.current.code, wanted.code, self.places)
        except Exception as error:
            # Raised inside the change, the save or the trees may have changed: an error, not a refusal.
            report.error_once("page:switch", f"the change stopped after an error: {error!r}")
            outcome = switch.Outcome(leave.ERROR)
        self.view = self._read(outcome, wanted)

    def cancel(self) -> None:
        if self.view.kind == CONFIRM:
            self.view = View(CARDS, True, self.view.current)

    def leave(self) -> bool:
        """RETURN TO MAIN MENU: True when the change is asked and the window must close for the return."""
        if self._moved():
            return False
        view = self.view
        if view.kind != CONFIRM:
            return False
        _, game, _ = self.where
        if leave.ask(game, view.current.code, view.wanted.code):
            # As leave.busy() now says: a second click must neither ask again nor bring the cards back.
            self.busy, self.view = True, View(BUSY, True)
            return True
        self.view = View(CARDS, True, view.current, said=switch.Outcome(leave.NO_RETURN), said_to=view.wanted)
        return False
