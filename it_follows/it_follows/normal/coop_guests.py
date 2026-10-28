"""The host's part for each co-op guest (decision 131): the damage the guest takes raised by the level (damage_taken.py)
and the guest's gains raised by its shares (rewards.py), on the guest's character in the host's game. Trial 74: the
host's game decides both; written there, the guest's experience doubled exactly while the guest's own copy read 1, and
both games read the same hits (vérifié en jeu). The guest's game writes neither (guest.py).

The Hardcore stays each hunter's own (Kevin, 18 October 2026: « le mod ne cumul pas les kill des autres chasseur de la
partie, uniquement les siens »): its factor lives in each player's game, and the host's game cannot read the guest's.
So the host asks each guest's game its percent when it raises the guest, and again every EVERY_S until it answers:
trial 79's first ask came while the guest's mode was starting its game again, and was lost. It tells it each enemy the
guest killed, and every EVERY_S the run of the host's level, which the guest's game writes on its copies of the
enemies (guest.py). It
gives the guest's damage taken the percent the guest's game answers (coop_messages.py, decision 133); until an answer,
the level's alone. The enemies' health takes the host's (Kevin: « celui de l'hote »), the enemies being the same for
all.

Every EVERY_S, while the game holds more players than the host and the guests held, the others are looked for
(presence.others); one new is raised. One held is kept while its character is there and a player's, even when a
search misses it: trial 75's searches missed the guest twice for 5 s, each time given back then raised again. Its
character no longer a player's, it is given back; gone, it is forgotten, having gone with what was written on it. At
the end each one held is given back. Where the guests held are, the
enemies are met for them too (play.py: the camps grown and the gestures watched around each player).
"""

import math
from typing import Any, Callable

import unrealsdk

from .. import damage_taken, hardcore_steps, presence
from ..characters import reads
from . import coop_messages, rewards

EVERY_S = 5.0
# The enemies this near a guest dodge at the game's speed (decision 132, trial 77): about the reach of a fight the guest
# sees, as WATCH_M is the hunter's (Claude's choice; the guest's view distance is not measured).
PLAIN_M = 100.0
# The asks again and the runs told written down by guest: a guest without the mode never answers, and is asked every
# EVERY_S; the run is told every EVERY_S, to a guest whose mode started its game again too.
SAID_ASKS = 3


class Guest:
    def __init__(self, actor: Any, taken: Any, gains: Any) -> None:
        self.pointer = unrealsdk.unreal.WeakPointer(actor)
        self.taken, self.gains = taken, gains
        self.percent: int | None = None
        self.asks = self.runs = 0


def _playing(guest: Guest) -> bool:
    actor = guest.pointer()
    return actor is not None and getattr(actor, "PlayerState", None) is not None


def _controller(actor: Any) -> Any:
    return getattr(actor, "Controller", None) if actor is not None else None


def _tell(announce: Callable[..., None], actor: Any, word: str, number: int = 0) -> str:
    """A word to the guest's game: told, or why not. A failure costs the guest its Hardcore, never the game."""
    controller = _controller(actor)
    if controller is None:
        return "no_controller"
    announce("ClientMessage", word=word, number=number)
    try:
        coop_messages.tell_guest(controller, word, number)
    except Exception as error:
        return f"failed:{type(error).__name__}"
    return "told"


class CoopGuests:
    """level: levels.Level; announce(call, **fields) notes each write before it is made."""

    def __init__(self, level: Any, announce: Callable[..., None]) -> None:
        self.level, self.announce = level, announce
        self.held: dict[str, Guest] = {}
        self.read_at = -math.inf

    def due(self, now: float) -> bool:
        return now - self.read_at >= EVERY_S

    def look(self, player: Any, now: float) -> dict:
        """The guests no longer players given back, the new raised: what was done, empty when nothing changed."""
        self.read_at = now
        gone = {name: self._give_back(self.held.pop(name)) for name in
                [name for name, guest in self.held.items() if not _playing(guest)]}
        count = presence.players() or 0
        raised = {}
        for actor in presence.others(player) if count > 1 + len(self.held) else []:
            name = reads.clean(getattr(actor, "Name", "?"))
            if name not in self.held:
                raised[name] = self._raise(name, actor)
        again = {name: self._ask(guest) for name, guest in self.held.items()
                 if guest.percent is None and name not in raised}
        again = {name: outcome for name, outcome in again.items() if outcome is not None}
        run = round(self.level.speed * 1000)
        for guest in self.held.values():
            guest.runs += 1
            said = guest.runs <= SAID_ASKS
            _tell(lambda *a, **k: self.announce(*a, log=said, **k), guest.pointer(), coop_messages.RUN, run)
        if not raised and not gone and not again:
            return {}
        return {"raised": raised, "gone": gone, "held": len(self.held), **({"asked_again": again} if again else {})}

    def _ask(self, guest: Guest) -> str | None:
        """A guest that never answered asked again: what was done, None once past SAID_ASKS."""
        guest.asks += 1
        said = guest.asks <= SAID_ASKS
        outcome = _tell(lambda *a, **k: self.announce(*a, log=said, **k), guest.pointer(), coop_messages.ASK)
        return outcome if said else None

    @staticmethod
    def _give_back(guest: Guest) -> dict:
        actor = guest.pointer()
        return {"taken": guest.taken.put_back(actor), "gains": guest.gains.put_back(actor)}

    def _raise(self, name: str, actor: Any) -> dict:
        guest = Guest(actor, damage_taken.DamageTaken(self.announce, self.level.taken),
                      rewards.Rewards(self.level, self.announce))
        self.held[name] = guest
        return {"taken": guest.taken.start(actor), "gains": guest.gains.start(actor),
                "asked": _tell(self.announce, actor, coop_messages.ASK)}

    def kills(self, by_others: dict[str, int]) -> dict[str, int | str]:
        """Each guest held told the enemies it killed, by the census's count of each character's kills: what each
        was told, or why not."""
        told: dict[str, int | str] = {}
        for name, count in by_others.items():
            guest = self.held.get(name)
            actor = guest.pointer() if guest is not None else None
            if actor is not None:
                count = min(count, coop_messages.MOST_KILLS)
                outcome = _tell(self.announce, actor, coop_messages.KILLS, count)
                told[name] = count if outcome == "told" else outcome
        return told

    def heard(self, percents: list[tuple[Any, int]]) -> dict:
        """Each guest's percent heard given to its damage taken, on top of the level: by guest, the percent and what
        the change did; the messages of no guest held counted."""
        done: dict = {}
        unknown = 0
        for pointer, percent in percents:
            controller = pointer()
            found = [(name, guest) for name, guest in self.held.items()
                     if controller is not None and _controller(guest.pointer()) == controller]
            if not found:
                unknown += 1
                continue
            name, guest = found[0]
            if percent == guest.percent:
                continue
            guest.percent = percent
            factor = self.level.taken * hardcore_steps.factor(percent)
            done[name] = {"percent": percent, "taken": guest.taken.change(guest.pointer(), factor)}
        if unknown:
            done["unknown"] = unknown
        return done

    def keep(self) -> dict:
        """Once a second, each guest's multiplier the game wrote anew raised again: what it did, by guest."""
        kept = {}
        for name, guest in self.held.items():
            actor = guest.pointer()
            if actor is not None:
                done = guest.taken.keep(actor)
                if done is not None:
                    kept[name] = done
        return kept

    def places(self) -> list[tuple]:
        """Where each guest held is, those that can be read."""
        found = []
        for guest in self.held.values():
            actor = guest.pointer()
            here = reads.point(actor) if actor is not None else None
            if here is not None:
                found.append(here)
        return found

    def end(self) -> dict:
        """Each guest held given back: by guest, its damage taken and its gains."""
        held, self.held = self.held, {}
        return {name: self._give_back(guest) for name, guest in held.items()}
