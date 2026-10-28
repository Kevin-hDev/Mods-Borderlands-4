"""The run's heartbeat: the game's animation update, hooked after each call, gives the run one sample a second.

The trials' samples and BL4 Arena's watches ran on this hook in game for minutes on end
(/Script/Engine.AnimInstance:BlueprintUpdateAnimation; docs/RUN/sondes/run_trial_kit.py, bl4_arena/births.py). The
game calls it many times an image, once for each animated character, so the beat lets one call a second through. Each
beat takes its place, under its own name, on the package's one hook on that update (characters/animation_hook.py,
audit of 24 October 2026). It stops coming while the game stands still: the run's clock reads the world's own time,
which stands still too. An error escaping a sample stops the run, rather than leave the enemies held by a run that no
longer looks after them.

A second's heavy work may be put off (defer) to the images that follow, one task an image: in trial 16 the run's whole
second, the enemies, the census and the game's camps, held one image 77 to 89 ms with 120 enemies (audit of 15 October
2026). A new image is known when the character whose update gave the last work is updated again, by its address only,
never holding it; LATER_MOST_S stands in should it be gone. How many times the game called the hook is counted, for
the status line, with what a call that has nothing to do takes in the beat (characters/beat_gauge.py; audit of 16
October 2026, A11); what the SDK spends handing each call to Python is not in it, and is read by
docs/RUN/sondes/run_hook_cost.py.
"""

import time
from typing import Any, Callable

from .characters import animation_hook, beat_gauge, game_thread

IDENTIFIER = "it_follows:run"
EVERY_S = 1.0
# A task put off waits at most this long for its image: a character gone is never updated again.
LATER_MOST_S = 0.05


def now() -> float:
    return time.monotonic()


def _address(obj: Any) -> int | None:
    try:
        return obj._get_address()
    except Exception:
        return None


class Beat:
    """tick(now) is called once a second at most; fail(reason) when a tick or a task put off raises. identifier: the
    beat's name, the normal mode's apart from a run's, so that one never takes the other's place."""

    def __init__(self, tick: Callable[[float], None], fail: Callable[[str], None],
                 identifier: str = IDENTIFIER) -> None:
        self.tick, self.fail, self.identifier = tick, fail, identifier
        self.hook: Any = None
        # Made with the hook, on the game's thread: a call that comes elsewhere does nothing (game_thread.py).
        self.guard: game_thread.Guard | None = None
        self.next = 0.0
        # The tasks put off, by name, in their order: one name is never waiting twice.
        self.later: dict[str, Callable[[float], None]] = {}
        self.marked: int | None = None
        self.marked_at = 0.0
        self.count = beat_gauge.Calls(now)

    def start(self) -> None:
        """Takes its place on the animation update; the first tick comes a second later."""
        self.next = now() + EVERY_S
        self.count = beat_gauge.Calls(now)
        self.guard = game_thread.Guard(self.identifier)
        self.hook = animation_hook.beat(self.identifier, self._frame)
        self.hook.enable()

    def defer(self, name: str, task: Callable[[float], None]) -> None:
        """task(now) run on a later image than the work before it; a name already waiting is not added again."""
        self.later.setdefault(name, task)

    def _frame(self, obj: Any = None, *_args: Any) -> None:
        if self.hook is None or (self.guard is not None and not self.guard.here()):
            return
        began = self.count.called()
        moment = now()
        if moment < self.next:
            if self.later and (moment - self.marked_at >= LATER_MOST_S
                               or (self.marked is not None and _address(obj) == self.marked)):
                name = next(iter(self.later))
                self._run(self.later.pop(name), moment, obj)
                return
            self.count.idle(began)
            return
        self.next = moment + EVERY_S
        self._run(self.tick, moment, obj)

    def _run(self, work: Callable[[float], None], moment: float, obj: Any) -> None:
        try:
            work(moment)
        except Exception as error:
            self.fail(f"error:{type(error).__name__}")
        self.marked, self.marked_at = _address(obj), now()

    def gauge(self) -> dict:
        """Since the last time asked: the hook's calls a second, and the µs a call with nothing to do took in the beat
        (None without one); then counted afresh."""
        return self.count.said()

    def stop(self) -> str:
        """Leaves the update, the tasks put off dropped: "removed", "inactive" when never set or left already, or
        "remove_failed"."""
        active, self.hook = self.hook, None
        self.later = {}
        if active is None:
            return "inactive"
        try:
            active.disable()
        except Exception:
            return "remove_failed"
        return "removed"
