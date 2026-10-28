"""The hunters being dressed for one team (dress.py), dressed from the camera's update, never from the animation's.

Dressing changes a character's meshes: his own draws the hunter's upper body, parts are added and hung on it, and
painted. Since the game's update of 22 October 2026 (build 4906557), dressing from the team's beat, on the animation
update, crashed the game on one of its worker threads half a second after a hunter was dressed: trials 198, 199,
206, 209 and 210, the same calls under the two at the top in four of them, with or without the names' package
(decision 65 of docs/renforts/README.md). That update comes while the game still works out the characters'
animations on its worker threads: twice, it came on one of them (trials 206 and 210). The camera's modifiers are
updated once every actor's work of the image is done (Unreal's world tick updates the cameras after all the
actors' ticks, déduction from the engine; called about six times an image in BL4, docs/meteo, trial of
5 October 2026, vérifié en jeu); the meshes change there.

A hunter is hidden from his start to his end, as dress.py does; one the camera's update never comes for within
START_WAIT_S is left as he is, Lemmy, and said: never a team waiting forever, never a mesh changed elsewhere.
"""

import math
from typing import Any, Callable

from mods_base import hook
from unrealsdk.hooks import Type

from .. import game_thread, report
from . import follow

HOOK = "/Script/Engine.CameraModifier:BlueprintModifyCamera"
# Named after the mod this copy ships in, as the team's hook (team.py).
IDENTIFIER = f"{__package__.split('.')[0]}:companions_dress"
# Claude's choice: a few hundred images; the camera's update comes several times each one.
START_WAIT_S = 5.0


class Wardrobe:
    """The dressings of one team: waiting for the camera's update to start, then being finished; most of each kept,
    the latest. clock() the team's time."""

    def __init__(self, clock: Callable[[], float], most: int) -> None:
        self.clock, self.most = clock, most
        # (character, companion, dress.Dressing, since when it waits), then (character, companion, dress.Dressing).
        self.waiting: list = []
        self.dressing: list = []
        self.hook: Any = None
        self.guard: game_thread.Guard | None = None

    def start(self) -> None:
        """The camera's update hooked, from the game's thread, as the team starts."""
        self.guard = game_thread.Guard("dress")
        self.hook = hook(HOOK, Type.POST, hook_identifier=IDENTIFIER)(self.frame)
        self.hook.enable()

    def add(self, character: str, companion: str, dressing: Any) -> str:
        """A hunter to dress at the camera's next update."""
        self.waiting = self.waiting[-(self.most - 1):] + [(character, companion, dressing, self.clock())]
        return "queued"

    def frame(self, *_args: Any) -> None:
        if self.hook is None or (self.guard is not None and not self.guard.here()):
            return
        # Those started at an earlier update first: one just given his upper body waits for the game to draw it.
        for held in list(self.dressing):
            self._step(held)
        waiting, self.waiting = self.waiting, []
        for character, companion, dressing, _since in waiting:
            self._started(character, companion, dressing)

    def _started(self, character: str, companion: str, dressing: Any) -> None:
        started = follow.tried(dressing.start)
        report.note("companion_dressing", character=character, companion=companion,
                    **(started if isinstance(started, dict) else {"done": started}))
        if isinstance(started, dict) and started["done"] == "swapped":
            self.dressing = self.dressing[-(self.most - 1):] + [(character, companion, dressing)]

    def _step(self, held: tuple) -> None:
        character, companion, dressing = held
        outcome = follow.tried(dressing.step)
        if outcome is None:
            return
        if not isinstance(outcome, dict):
            follow.tried(dressing.give_up)
            outcome = {"done": outcome}
        self.dressing.remove(held)
        report.note("companion_dressed", character=character, companion=companion, **outcome)

    def due(self) -> float:
        """When overdue has someone to leave as he is: the first waiting one's START_WAIT_S."""
        return min((since + START_WAIT_S for *_held, since in self.waiting), default=math.inf)

    def overdue(self) -> None:
        """Called from the team's beat: those the camera's update never came for within START_WAIT_S left as they
        are, said."""
        now, kept = self.clock(), []
        for character, companion, dressing, since in self.waiting:
            if now - since < START_WAIT_S:
                kept.append((character, companion, dressing, since))
                continue
            report.note("companion_dressing", character=character, companion=companion, done="camera_never_came",
                        waited_s=round(now - since, 2))
        self.waiting = kept

    def stop(self) -> None:
        """Every hunter being dressed given up (shown again), those waiting forgotten, the hook removed whatever
        failed before."""
        try:
            for _character, _companion, dressing in self.dressing:
                follow.tried(dressing.give_up)
        finally:
            self.waiting, self.dressing = [], []
            if self.hook is not None:
                self.hook.disable()
                self.hook = None
