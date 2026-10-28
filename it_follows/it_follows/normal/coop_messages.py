"""The messages between the host's normal mode and each co-op guest's, for the Hardcore (decision 133): each hunter
counts his own kills (Kevin, 18 October 2026: « le mod ne cumul pas les kill des autres chasseur de la partie,
uniquement les siens »), the host's game sees who killed each enemy, and computes the guest's damage taken.

Both ways verified in game (trial 78, docs/RUN/enquetes/2026-10-18-essai-78-canal-du-hardcore.md), each answered within
some 40 ms:
- the host to a guest: the engine's ClientMessage, a text of MARK, kept by the guest's mod from its game (docs/coop,
  trial 3: never seen on screen even let through);
- a guest to the host: the engine's ServerSetSpectatorLocation, a place whose X is MARK_X and Y the guest's percent,
  kept by the host's mod from its game. The grapple's message, Apex Grapple's, is never used: its host takes any
  message of no target for a rope (apex_grapple/coop_host.py).

The host also tells each guest the run its level gives the enemies (RUN, in thousandths), so that the guest's game
writes the host's on its copies, never its own (guest.py): the guest's own level may be another, or REDUCED.

A guest speaks only in answer to the host, whose mod then plays and keeps the message from the game. Each message is
read in the game's network call and acted on at the mode's next second, as Apex Grapple's are: what it does (a write
to the settings file, the damage taken) belongs to the game's frame. What comes from the other game is checked before
use: a text of MARK with one known word and a whole number in bounds, a percent whole and in bounds; anything else is
let through to the game, untouched.
"""

from typing import Any

import unrealsdk
from mods_base import hook
from unrealsdk.hooks import Block, Type

IDENTIFIER = "it_follows:normal_coop"
TO_HOST = "/Script/Engine.PlayerController:ServerSetSpectatorLocation"
TO_GUEST = "/Script/Engine.PlayerController:ClientMessage"
# No place of a level: 9 km below the ground of any map read so far.
MARK_X = -917531.0
MARK = "ItFollows:"
ASK, KILLS, RUN = "ask", "kills", "run"
# A census reads at most some 200 enemies (enemies.MOST); hardcore.MOST_KILLS is 10 000 percent.
MOST_KILLS = 1000
MOST_PERCENT = 10_000
# The run in thousandths: the game's own (1.0) to twice it, the levels' being 1.2 to 1.5 (levels.py).
RUN_LEAST, RUN_MOST = 1000, 2000
# Messages kept until the next second: four players, a few each.
MAX_PENDING = 16


def read_text(text: str) -> tuple[str, int] | None:
    """A guest's reading of a host's text: (ASK, 0), (KILLS, n), (RUN, thousandths), or None for one not ours or
    out of bounds."""
    if not text.startswith(MARK) or len(text) > 40:
        return None
    word, _, number = text[len(MARK):].partition(" ")
    if word == ASK and not number:
        return ASK, 0
    if word == KILLS and number.isdigit() and 0 < int(number) <= MOST_KILLS:
        return KILLS, int(number)
    if word == RUN and number.isdigit() and RUN_LEAST <= int(number) <= RUN_MOST:
        return RUN, int(number)
    return None


def read_percent(x: float, y: float) -> int | None:
    """A host's reading of a guest's place: its percent, or None for one not ours or out of bounds."""
    if abs(x - MARK_X) >= 0.5 or not 0.0 <= y <= MOST_PERCENT or y != int(y):
        return None
    return int(y)


class Link:
    """One side's door: on the host the guests' percents heard, on a guest the host's texts heard, each kept for the
    next second. Hooked from start to stop only."""

    def __init__(self, host: bool) -> None:
        self.host = host
        self.pending: list[tuple[Any, Any]] = []
        self.dropped = 0
        self.hook: Any = None

    def start(self) -> None:
        path, heard = (TO_HOST, self._heard_guest) if self.host else (TO_GUEST, self._heard_host)
        self.hook = hook(path, Type.PRE, hook_identifier=IDENTIFIER)(heard)
        self.hook.enable()

    def stop(self) -> str:
        active, self.hook = self.hook, None
        self.pending = []
        if active is None:
            return "inactive"
        try:
            active.disable()
        except Exception:
            return "remove_failed"
        return "removed"

    def take(self) -> list[tuple[Any, Any]]:
        """What was heard since the last second: (controller's weak pointer, percent) on the host, (None, (word,
        number)) on a guest."""
        pending, self.pending = self.pending, []
        return pending

    def _keep(self, entry: tuple[Any, Any]) -> None:
        if len(self.pending) < MAX_PENDING:
            self.pending.append(entry)
        else:
            self.dropped += 1

    def _heard_guest(self, obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
        try:
            percent = read_percent(float(args.NewLoc.X), float(args.NewLoc.Y))
        except Exception:
            return None
        if percent is None:
            return None
        self._keep((unrealsdk.unreal.WeakPointer(obj), percent))
        return Block

    def _heard_host(self, _obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
        try:
            said = read_text(str(args.S))
        except Exception:
            return None
        if said is None:
            return None
        self._keep((None, said))
        return Block


def tell_guest(controller: Any, word: str, number: int = 0) -> None:
    """The host to one guest's game."""
    controller.ClientMessage(MARK + word + ("" if word == ASK else f" {number}"), "None", 0.0)


def tell_host(pc: Any, percent: int) -> None:
    """A guest to the host: its Hardcore's percent."""
    pc.ServerSetSpectatorLocation(unrealsdk.make_struct("Vector", X=MARK_X, Y=float(percent), Z=0.0),
                                  unrealsdk.make_struct("Rotator", Pitch=0.0, Yaw=0.0, Roll=0.0))
