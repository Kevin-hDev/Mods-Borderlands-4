"""The combat radius of the zone lent to the horde, widened while a run lasts and written back when it stops.

Trial 6p (decision 33): with the lent zone made 600 m wide, the enemies left alone stopped three to four times less
often between 100 and 200 m from the hunter. The writer is the enemy research's (mods/perso/apex_probe/
apex_territory_radius_patch.py), which wrote that radius in game in its sessions 11 and 36; It Follows keeps its own
copy (decision 45) and reads the radius as the census does (reads.zone_radius_cm). Only a radius the run still owns is
written back: one the game changed meanwhile is left as the game set it.
"""

import math
from typing import Any

from . import reads

MIN_RADIUS_CM = 100.0
MAX_RADIUS_CM = 100_000.0


def _path(target: Any) -> str:
    try:
        return str(target._path_name())
    except Exception as error:
        raise ValueError("territory identity unavailable") from error


def _area(target: Any) -> Any:
    try:
        return target.settings.CombatTerritory
    except Exception as error:
        raise ValueError("combat territory unavailable") from error


class TerritoryRadiusPatch:
    """One zone's combat radius made target_radius_cm, its own written back once, only on the same zone and while the
    radius written is still there. A radius outside MIN_RADIUS_CM to MAX_RADIUS_CM, asked or found, raises
    ValueError."""

    def __init__(self, target_radius_cm: float) -> None:
        value = float(target_radius_cm)
        if not math.isfinite(value) or not MIN_RADIUS_CM <= value <= MAX_RADIUS_CM:
            raise ValueError("invalid target radius")
        self.target = value
        self.saved: tuple[str, float] | None = None

    def apply(self, territory: Any) -> float:
        """Writes the radius and reads it back; says the radius the zone had. A write the game does not keep raises, the
        zone's own radius written back first."""
        if self.saved is not None:
            raise RuntimeError("territory patch already active")
        path = _path(territory)
        before = reads.zone_radius_cm(territory)
        if not MIN_RADIUS_CM <= before <= MAX_RADIUS_CM:
            raise ValueError("unsupported original radius")
        _area(territory).Radius = self.target
        if reads.zone_radius_cm(territory) != self.target:
            _area(territory).Radius = before
            raise RuntimeError("territory write verification failed")
        self.saved = path, before
        return before

    def restore(self, territory: Any) -> str:
        """Writes the zone's own radius back, once: restored or restore_failed; inactive when nothing was written,
        different_territory, ownership_lost when the game changed the radius meanwhile, unavailable when unreadable."""
        saved, self.saved = self.saved, None
        if saved is None:
            return "inactive"
        try:
            if _path(territory) != saved[0]:
                return "different_territory"
            if reads.zone_radius_cm(territory) != self.target:
                return "ownership_lost"
            _area(territory).Radius = saved[1]
            return "restored" if reads.zone_radius_cm(territory) == saved[1] else "restore_failed"
        except ValueError:
            return "unavailable"
        except Exception:
            return "restore_failed"
