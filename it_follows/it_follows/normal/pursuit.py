"""The level's long chase (decision 80): the combat radius of each enemy's own zone widened to the level's, so that it
follows the player farther before going home, and written back when the game is left or the mode stops.

Kevin, 15 October 2026: « 250m c'est pas long, poursuite on peu pousser a 350m pour bandit/senior ». The game still
takes an enemy home when the player goes too far from its camp (570 m to 1 km, the Horde's trials): the chase keeps an
end. The writer is the Horde's (zone_radius.py), whose wide zone made enemies stop three to four times less often
(trial 6p). A zone is shared by its camp's enemies: it is widened once, held by its path and a weak pointer, since the
game loads a place's zones again under the same path. A zone already as wide is left alone.
"""

from typing import Any, Callable

import unrealsdk

from .. import zone_radius

# Zones held at once: the census reads every enemy the game holds, all within some 360 m of the player (trial 1). The
# zones the game freed are forgotten before this refuses (audit of 15 October 2026).
MOST = 256


class Pursuit:
    """announce(call, log, **fields) notes a write before it is made."""

    def __init__(self, announce: Callable[..., None], chase_m: float) -> None:
        self.announce = announce
        self.target_cm = chase_m * 100.0
        # By path: the zone's weak pointer, and its writer, None for a zone left as it was.
        self.zones: dict[str, tuple[Any, zone_radius.TerritoryRadiusPatch | None]] = {}

    def widened(self) -> int:
        return sum(1 for _, patch in self.zones.values() if patch is not None)

    def widen(self, seen: Any) -> str:
        """The zone of an enemy the census read (seen.Seen) widened once: what was done."""
        if seen.zone is None:
            return "no_zone"
        held = self.zones.get(seen.zone_path)
        if held is not None and held[0]() is not None:
            return "already"
        if held is None and len(self.zones) >= MOST and not self._forget_gone():
            return "full"
        pointer = unrealsdk.unreal.WeakPointer(seen.zone)
        if seen.radius_m * 100.0 >= self.target_cm:
            self.zones[seen.zone_path] = (pointer, None)
            return "wide_enough"
        patch = zone_radius.TerritoryRadiusPatch(self.target_cm)
        self.announce("CombatTerritory.Radius", log=False, zone=seen.zone_path)
        try:
            patch.apply(seen.zone)
        except Exception as error:
            self.zones[seen.zone_path] = (pointer, None)
            return f"failed:{type(error).__name__}"
        self.zones[seen.zone_path] = (pointer, patch)
        return "widened"

    def _forget_gone(self) -> bool:
        """The zones the game freed forgotten: one loaded again comes with its own radius. Whether there is room now."""
        for path in [path for path, (pointer, _) in self.zones.items() if pointer() is None]:
            del self.zones[path]
        return len(self.zones) < MOST

    def narrow(self) -> dict:
        """Each zone still there given its radius back (zone_radius.restore); what was done, counted."""
        tally: dict[str, int] = {}
        for pointer, patch in self.zones.values():
            if patch is None:
                continue
            zone = pointer()
            status = "gone" if zone is None else patch.restore(zone)
            tally[status] = tally.get(status, 0) + 1
        self.zones = {}
        return tally
