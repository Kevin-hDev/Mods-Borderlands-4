"""The game's own camps around the hunter made critical during a run, and given back at the stop (decision 64).

Why: the game lets at most some 29 enemies of ordinary requests live at once, whatever bDisableSpawnBudget says, and
only requests made critical pass beyond (domed arena, lots trials 1 to 3: 29 alive at most of 50, then 48 of 50 once
critical; docs/spawn-boss/enquetes/2026-10-11-ennemis-par-lots.md). It Follows' copies are critical: in trial 12, some
35 to 87 of them alive, the places the hunter crossed stayed empty, while in trial 11, with no copies, they filled
(docs/RUN/enquetes/2026-10-14-essai-12-zones-pleines.md). That the copies take the room of the game's enemies is the
likely cause, not verified; trial 13 checks this lever. The flags were written on 179 camps in trial 6w without a crash
and read back, which is the recipe used here (docs/RUN/sondes/run_wake.py).

Only the camps within RANGE_M are written, so that a camp is critical before the hunter comes near enough to wake it
(80 to 300 m read in trial 6u); a camp already critical is left alone, and not given back. It Follows' own camps are
left out. The game waits while the camps are read: a pass stops at READ_S, the rest taken at the next pass. The
camps are those of the world in play (reads.search): trial 38 found the same ones as among every object the game
holds, but for 2 or 3 the game was unloading, some 10 ms sooner (decision 105).

A camp is held by its name, so that it is written once, but a name held is no proof that the camp is the same: the
game unloads the camps of a place the hunter left and, as trial 14 points to, loads them again when he comes back under
the same name, one of the map (OakSpawner_UAID_…), as new camps with the map's own flags. In trial 14 the hunter came
back to the place of the start after a fast travel: no camp was made critical after it, and at the stop none of the 563
held still lived. A name whose camp the game freed is read again as a new camp.
"""

import time
from itertools import islice
from typing import Any, Callable

from unrealsdk.unreal import WeakPointer

from . import reads

EVERY_S = 10.0
RANGE_M = 1000.0
# Trial 6u read 221 camps held and wrote 156 in 19 ms.
READ_S = 0.05
MAX_CAMPS = 3000
# At most this many camps held at once: trial 6u found 220. The camps the game freed are forgotten before this refuses:
# counted, they filled it after some 2 000 met, 26 minutes of trial 13's travel (771 in 603 s), and no camp was made
# critical from then on (audit of 15 October 2026).
MAX_HELD = 2000
SPAWNER_CLASS = "Spawner"


def _critical(component: Any) -> bool:
    details = component.SpawnDetails
    return bool(details.bCritical) and bool(details.bOverrideCritical)


def _write(component: Any, critical: bool, override: bool) -> bool:
    """The flags written, the struct given back whole as the game takes it; whether they read back."""
    details = component.SpawnDetails
    details.bCritical, details.bOverrideCritical = critical, override
    component.SpawnDetails = details
    now = component.SpawnDetails
    return bool(now.bCritical) == critical and bool(now.bOverrideCritical) == override


class GameCamps:
    """One run's camps made critical: each held weakly with its own flags, to give back. announce(call, log, **fields)
    notes a call before it is made; ours(name) says whether a camp is It Follows' own."""

    def __init__(self, announce: Callable[..., None], ours: Callable[[str], bool]) -> None:
        self.announce, self.ours = announce, ours
        self.held: dict[str, tuple[Any, bool, bool]] = {}
        self.woken_at = -float("inf")

    def due(self, now: float) -> bool:
        return now - self.woken_at >= EVERY_S

    def wake(self, here: tuple | None, now: float, world: Any = None) -> dict:
        """The camps within RANGE_M of here made critical; what the pass found, and how the camps were searched.
        world: an actor of the world in play, the hunter."""
        self.woken_at = now
        counts = dict.fromkeys(("read", "made", "remade", "already", "ours", "far", "not_read_back", "unreadable"),
                               0)
        stopped, began = "complete", time.monotonic()
        if here is None:
            return {**counts, "stopped": "no_place", "search": None}
        self.announce("SpawnDetails critical", game_camps=len(self.held))
        spawners, search = reads.search(SPAWNER_CLASS, world)
        for spawner in islice(spawners, MAX_CAMPS):
            if time.monotonic() - began > READ_S:
                stopped = "time_limit"
                break
            name = reads.clean(getattr(spawner, "Name", ""))
            if name.startswith("Default__"):
                continue
            again = name in self.held
            if again and self.held[name][0]() is not None:
                continue
            counts["read"] += 1
            if self.ours(name):
                counts["ours"] += 1
                continue
            metres = reads.metres(reads.point(spawner), here)
            if metres is None or metres > RANGE_M:
                counts["far"] += 1
                continue
            if len(self.held) >= MAX_HELD and not self._forget_gone():
                stopped = "held_limit"
                break
            try:
                component = spawner.SpawnerComponent
                if _critical(component):
                    counts["already"] += 1
                    continue
                details = component.SpawnDetails
                own = (bool(details.bCritical), bool(details.bOverrideCritical))
                done = _write(component, True, True)
            except Exception:
                counts["unreadable"] += 1
                continue
            self.held[name] = (WeakPointer(spawner), *own)
            counts["made" if done else "not_read_back"] += 1
            if done and again:
                counts["remade"] += 1
        return {**counts, "held": len(self.held), "stopped": stopped, "search": search,
                "took_ms": round((time.monotonic() - began) * 1000.0, 1)}

    def _forget_gone(self) -> bool:
        """The camps the game freed forgotten: nothing is left to give them back. Whether there is room now."""
        for name in [name for name, (pointer, _, _) in self.held.items() if pointer() is None]:
            del self.held[name]
        return len(self.held) < MAX_HELD

    def put_back(self) -> dict:
        """Each camp's own flags written back; those the game no longer holds are counted."""
        result = dict.fromkeys(("restored", "gone", "failed"), 0)
        if self.held:
            self.announce("SpawnDetails given back", game_camps=len(self.held))
        for pointer, critical, override in self.held.values():
            spawner = pointer()
            if spawner is None:
                result["gone"] += 1
                continue
            try:
                done = _write(spawner.SpawnerComponent, critical, override)
            except Exception:
                done = False
            result["restored" if done else "failed"] += 1
        self.held = {}
        return result
