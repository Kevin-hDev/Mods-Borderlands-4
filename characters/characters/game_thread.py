"""The game's thread: the only one a hook of the mod may touch the game from.

The animation update (/Script/Engine.AnimInstance:BlueprintUpdateAnimation) came on the game's thread at every trial
until trial 206 (22 October 2026): one call came on another thread, the team's beat ran there, dressed a hunter, and
the game crashed reading address 0x8 (docs/renforts, decision 62). Each hook keeps a Guard and does nothing from a
call that comes on another thread than the game's.

The thread a hook is set from is not always the game's: the mod's load runs on its own thread (trial 207, lost loot
and colours set there). So the game's thread is known once a hook is called on the thread it was set from; a hook set
elsewhere takes the game's thread once known, or the thread of its first call until then.
"""

import threading
from typing import Any, Callable

from . import report

# The game's thread once a hook was called on the thread it was set from.
_game: list[int | None] = [None]


def _said(event: str, **fields: Any) -> None:
    report.note(event, **fields)


class Guard:
    """here() whether this call comes on the game's thread; the calls elsewhere counted (away), the first said, so
    that the log tells it without a line at each image."""

    def __init__(self, what: str, say: Callable[..., None] = _said) -> None:
        self.what, self.say = what, say
        self.thread = threading.get_native_id()
        self.sure = False
        self.away = 0

    def here(self) -> bool:
        thread = threading.get_native_id()
        if not self.sure:
            self._learn(thread)
        if thread == self.thread:
            return True
        self.away += 1
        if self.away == 1:
            # In hexadecimal, as the SDK's log shows each line's thread.
            self.say("hook_off_thread", what=self.what, thread=f"{thread:x}", game=f"{self.thread:x}")
        return False

    def _learn(self, thread: int) -> None:
        self.sure = True
        if thread == self.thread:
            _game[0] = thread
        elif _game[0] is not None:
            self.thread = _game[0]
        else:
            # Set at the mod's load, the game's thread not known yet: the first call tells it, said.
            self.say("hook_thread_taken", what=self.what, thread=f"{thread:x}", set_from=f"{self.thread:x}")
            self.thread = thread
