"""The zone lent to the horde, or a camp's spawner, moved so that it stands on the hunter, then put back where it stood.

A zone is a scene component: its centre is read with K2_GetComponentLocation and it is moved with K2_SetWorldLocation,
the AndRotation form of which our mods call in game (benefix_ohm_attack beam.py, apex_grapple rope_pose.py): no sweep,
a HitResult for the out parameter the SDK requires, teleported. A camp's spawner is a whole actor (trial 6h), read with
K2_GetActorLocation and moved with K2_SetActorLocation, which takes the same parameters and moved the arena's dome and
spawners in game (docs/spawn-boss/sondes/spawn_move.py). A zone is put back whatever happens to the enemies: it belongs
to its group's spawner, not to one body. Taken from the trials' docs/RUN/sondes/run_zone_shift.py.
"""

import math
from typing import Any, Callable

import unrealsdk

from . import reads

# A zone read back within 1 m of the point asked counts as moved: moving one does not snap it to a grid.
PLACED_CM = 100.0


class Shift:
    """One zone, or with actor an actor, where it stood, and whether it was moved."""

    def __init__(self, zone: Any, actor: bool = False) -> None:
        self.zone = unrealsdk.unreal.WeakPointer(zone)
        self.getter, self.setter = (("K2_GetActorLocation", "K2_SetActorLocation") if actor
                                    else ("K2_GetComponentLocation", "K2_SetWorldLocation"))
        self.home = reads.point(zone, self.getter)
        self.moved = False

    def where(self) -> tuple | None:
        return reads.point(self.zone(), self.getter)

    def _move(self, zone: Any, at: tuple) -> bool:
        x, y, z = at
        getattr(zone, self.setter)(NewLocation=unrealsdk.make_struct("Vector", X=x, Y=y, Z=z), bSweep=False,
                                   SweepHitResult=unrealsdk.make_struct("HitResult"), bTeleport=True)
        reached = reads.point(zone, self.getter)
        return reached is not None and math.dist(reached, at) <= PLACED_CM

    def place(self, at: tuple | None, announce: Callable[[], None]) -> str:
        """Moves the zone onto at, the call announced first; says whether it stands there now. A failing call raises,
        the zone counted as moved so that it is put back."""
        zone = self.zone()
        if zone is None or self.home is None or at is None:
            return "unavailable"
        announce()
        self.moved = True
        return "moved" if self._move(zone, at) else "not_moved"

    def put_back(self, announce: Callable[[], None]) -> str:
        """Moves the zone back where it stood, once it was moved; one that did not get back is tried again next time."""
        if not self.moved:
            return "inactive"
        zone = self.zone()
        if zone is None:
            return "unavailable"
        try:
            announce()
            back = self._move(zone, self.home)
        except Exception as error:
            return f"restore_error:{type(error).__name__}"
        self.moved = not back
        return "restored" if back else "restore_failed"
