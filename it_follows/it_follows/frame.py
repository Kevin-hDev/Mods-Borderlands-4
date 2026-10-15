"""The run's heartbeat: the game's animation update, hooked after each call, gives the run one sample a second.

The trials' samples and BL4 Arena's watches ran on this hook in game for minutes on end
(/Script/Engine.AnimInstance:BlueprintUpdateAnimation; docs/RUN/sondes/run_trial_kit.py, bl4_arena/births.py). The
game calls it many times an image, once for each animated character, so the beat lets one call a second through. It
stops coming while the game stands still: the run's clock reads the world's own time, which stands still too. An
error escaping a sample stops the run, rather than leave the enemies held by a run that no longer looks after them.

A second's heavy work may be put off (defer) to the images that follow, one task an image: in trial 16 the run's whole
second, the enemies, the census and the game's camps, held one image 77 to 89 ms with 120 enemies (audit of 15 October
2026). A new image is known when the character whose update gave the last work is updated again, by its address only,
never holding it; LATER_MOST_S stands in should it be gone. How many times the game called the hook is counted, for
the status line: each call costs the game whatever the beat does with it, a cost never measured yet.
"""

import time
from typing import Any, Callable

from mods_base import hook
from unrealsdk.hooks import Type

HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
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
    hook's name, the normal mode's apart from a run's, so that one never takes the other's place."""

    def __init__(self, tick: Callable[[float], None], fail: Callable[[str], None],
                 identifier: str = IDENTIFIER) -> None:
        self.tick, self.fail, self.identifier = tick, fail, identifier
        self.hook: Any = None
        self.next = 0.0
        # The tasks put off, by name, in their order: one name is never waiting twice.
        self.later: dict[str, Callable[[float], None]] = {}
        self.marked: int | None = None
        self.marked_at = 0.0
        self.calls = 0
        self.counted_at = now()

    def start(self) -> None:
        """Hooks the animation update; the first tick comes a second later."""
        self.next = now() + EVERY_S
        self.counted_at = now()
        self.hook = hook(HOOK, Type.POST, hook_identifier=self.identifier)(self._frame)
        self.hook.enable()

    def defer(self, name: str, task: Callable[[float], None]) -> None:
        """task(now) run on a later image than the work before it; a name already waiting is not added again."""
        self.later.setdefault(name, task)

    def _frame(self, obj: Any = None, *_args: Any) -> None:
        if self.hook is None:
            return
        self.calls += 1
        moment = now()
        if moment < self.next:
            if self.later and (moment - self.marked_at >= LATER_MOST_S
                               or (self.marked is not None and _address(obj) == self.marked)):
                name = next(iter(self.later))
                self._run(self.later.pop(name), moment, obj)
            return
        self.next = moment + EVERY_S
        self._run(self.tick, moment, obj)

    def _run(self, work: Callable[[float], None], moment: float, obj: Any) -> None:
        try:
            work(moment)
        except Exception as error:
            self.fail(f"error:{type(error).__name__}")
        self.marked, self.marked_at = _address(obj), now()

    def calls_per_s(self) -> float:
        """The hook's calls a second since the last time asked."""
        moment = now()
        spent, calls = moment - self.counted_at, self.calls
        self.calls, self.counted_at = 0, moment
        return round(calls / spent, 1) if spent > 0.0 else 0.0

    def stop(self) -> str:
        """Unhooks the update, the tasks put off dropped: "removed", "inactive" when never hooked or unhooked already,
        or "remove_failed"."""
        active, self.hook = self.hook, None
        self.later = {}
        if active is None:
            return "inactive"
        try:
            active.disable()
        except Exception:
            return "remove_failed"
        return "removed"
