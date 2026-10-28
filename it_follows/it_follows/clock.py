"""The time a run has been played: the world's time (GameplayStatics.GetTimeSeconds), added up across worlds. It stands
still while the game is paused, whoever paused it: It Follows' window, the game's own menu.

Kevin, 15 October 2026: « non le temps passer dans le menu ne doit pas etre compabilisé ». The clock first read the
world's unpaused time and took off only the time It Follows' window held the pause: in trial 18 the game stood still
142 s outside the window, every mod silent, and those 142 s were counted. Under the window the world's time read 0.0 s
at every release the logs of trials 18 to 32 hold where the pause held, while the unpaused and the real time ran
(game_pause.release's line); where it was lost (trials 20 and 29), the world ran 0.45 to 0.91 s, rightly counted.
Whether the map pauses the game is not known: trial 9 (docs/RUN/enquetes/2026-10-14-barre-en-jeu.md) read the
unpaused time, which runs on through a pause. It is read through the player's controller, which stays while he
drives, unlike his character. A new world's time starts again from nothing, and all of it counts; a world never read
is never taken for a new one, or all the time it has run would count at once. For a sample where the world's time
cannot be read, the real time stands in.
"""

import math
from typing import Any

import mods_base
import unrealsdk

# Samples come once a second: a longer wait between two is worth a line in the log, with what each clock did.
GAP_S = 2.0


def _world() -> Any:
    try:
        return mods_base.ENGINE.GameViewport.World
    except Exception:
        return None


def _world_time(pc: Any) -> float | None:
    try:
        value = float(unrealsdk.find_class("GameplayStatics").ClassDefaultObject.GetTimeSeconds(pc))
    except Exception:
        return None
    return value if math.isfinite(value) else None


class Clock:
    """The time played since the run began, in seconds (played), and how many samples the real time had to time."""

    def __init__(self, pc: Any, now: float) -> None:
        self.played = 0.0
        self.fallbacks = 0
        self.real_at, self.world_at = now, _world_time(pc)
        world = _world()
        self.world = unrealsdk.unreal.WeakPointer(world) if world is not None else None

    def _same(self, world: Any) -> bool:
        old = self.world() if self.world is not None else None
        return old is not None and old == world

    def tick(self, pc: Any, now: float) -> dict:
        """Adds the world's time gone by since the last sample; says what each clock did, and whether the world is
        new."""
        world, world_time = _world(), _world_time(pc)
        real_gap = now - self.real_at
        new_world = world is not None and self.world is not None and not self._same(world)
        if world_time is not None and new_world:
            world_gap = world_time
        elif world_time is not None and self.world_at is not None and world_time >= self.world_at:
            world_gap = world_time - self.world_at
        else:
            world_gap = None
        if world_gap is None:
            self.fallbacks += 1
        self.played += max(0.0, real_gap if world_gap is None else world_gap)
        self.real_at, self.world_at = now, world_time
        if world is not None:
            self.world = unrealsdk.unreal.WeakPointer(world)
        return {"real_gap_s": round(real_gap, 2), "world_gap_s": None if world_gap is None else round(world_gap, 2),
                "new_world": new_world}
