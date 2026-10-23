"""The companions asked of their spawners and not found yet when their team stops (review of 23 October 2026): each is
born a moment later (0.16 s once, trial 212's log) and would stand in the world unfollowed, a hunter as Lemmy
undressed, until the map changes. Each is looked for, born of its spawner, for FIND_S of play after the stop, then
taken out of the world as a stopped team's companions are (leave.py). Not at the main menu: the world goes with them
(team.py).

Only the time the game runs counts (each beat counts at most MAX_STEP_S): a window holding the pause, or a map
loading, would otherwise use it up before the companion could be born. A spawner a team asks again is watched no
more (forget, called by team.py at each ask): what it bears from then on is that team's.

One watch for this copy of the package, with a hook of its own named after the mod (team.py gives the name): a team
started meanwhile keeps its own hook, and the watch, ending, removes only its own. MOST looked for at most, the
oldest dropped first. Its hook stays at most FIND_S of play after the team's stop, the mod switched off included.
"""

from typing import Any, Callable

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from .. import game_thread, report
from . import choose, fight, kinds, leave, respawn, world
from .zone import zone_of

# Two teams' worth: a team stopped, another started and stopped within FIND_S.
MOST = 2 * kinds.MOST
MAX_TEXT = 120
# The most one beat counts: the animation update comes at each frame while the game runs.
MAX_STEP_S = 0.25


class Strays:
    def __init__(self, clock: Callable[[], float]) -> None:
        self.clock = clock
        # Each one looked for: its companion, its spawner, the play time left to look for it.
        self.looked: list[dict] = []
        self.hook: Any = None
        self.guard: game_thread.Guard | None = None
        self.last: float | None = None
        self.next = 0.0

    def add(self, asked: list[tuple[str, str, float]], hook_name: str, identifier: str) -> None:
        """Those to look for, and the hook set if none is."""
        fresh = [{"companion": companion, "spawner": spawner, "left_s": respawn.FIND_S}
                 for companion, spawner, _asked in asked]
        self.looked = (self.looked + fresh)[-MOST:]
        report.note("strays_watched", companions=[one["companion"] for one in fresh], looked=len(self.looked))
        if self.hook is None and self.looked:
            self.guard = game_thread.Guard("strays")
            self.last = None
            self.hook = hook(hook_name, Type.POST, hook_identifier=identifier)(self.beat)
            self.hook.enable()

    def forget(self, spawner: str) -> None:
        self.looked = [one for one in self.looked if one["spawner"] != spawner]

    def beat(self, *_args: Any) -> None:
        if self.guard is not None and not self.guard.here():
            return
        now = self.clock()
        step = 0.0 if self.last is None else min(max(now - self.last, 0.0), MAX_STEP_S)
        self.last = now
        for one in self.looked:
            one["left_s"] -= step
        if now < self.next and self.looked:
            return
        self.next = now + respawn.FIND_EVERY_S
        try:
            self._look()
        finally:
            if not self.looked:
                self.off()

    def _look(self) -> None:
        try:
            pc = get_pc()
            here = world.place(world.hunter(pc))
            characters = [] if here is None else fight.characters(pc)
        except Exception as error:
            # Nothing read this time: those looked for still give up once their time is used.
            report.error_once("strays_read", f"the companions left on their way could not be looked for: "
                              f"{type(error).__name__}")
            here, characters = None, []
        for one in list(self.looked):
            kind = kinds.BY_NAME.get(one["companion"])
            try:
                actor = None if kind is None or here is None else choose.choose(
                    characters, world, zone_of, kind.definition, here, one["spawner"])[0]
            except Exception as error:
                self._drop(one, "stray_lost", why=f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}")
                continue
            if actor is not None:
                self._drop(one, "stray_removed", removed=leave.leave(actor, str(actor.Name), report.announce))
            elif kind is None or one["left_s"] <= 0.0:
                self._drop(one, "stray_lost", why="not_found")

    def _drop(self, one: dict, event: str, **fields: Any) -> None:
        self.looked.remove(one)
        report.note(event, companion=one["companion"], spawner=one["spawner"], **fields)

    def off(self) -> None:
        if self.hook is not None:
            self.hook.disable()
            self.hook = None


_watch: dict[str, Strays | None] = {"strays": None}


def watch(asked: list[tuple[str, str, float]], clock: Callable[[], float], hook_name: str, identifier: str) -> None:
    """Those a stopped team had asked, looked for until each is found or FIND_S of play passed."""
    if not asked:
        return
    strays = _watch["strays"]
    if strays is None:
        strays = _watch["strays"] = Strays(clock)
    strays.clock = clock
    strays.add(asked, hook_name, identifier)


def forget(spawner: str) -> None:
    """A spawner a team asks again: watched no more, the companion it bears being that team's."""
    strays = _watch["strays"]
    if strays is not None:
        strays.forget(spawner)


def reset_for_tests() -> None:
    strays = _watch["strays"]
    if strays is not None:
        strays.off()
    _watch["strays"] = None
