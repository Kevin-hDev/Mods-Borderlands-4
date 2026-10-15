"""The camp each enemy of the horde comes from: the game's spawner that owns its zone (trial 6g), noted by name and held
through a weak pointer, for the camps that follow the hunter (camp_follow.py).

A zone is a part of its spawner: its Outer is the spawner, which carries a SpawnerComponent. An enemy is forgotten once
it leaves the horde (forget_enemy), a camp once it is let go of (forget): over a run of an hour, neither table holds
more than the run does. Taken from the trials' docs/RUN/sondes/run_camp_watch.py, without its reads of the spawners'
settings, which only served the trials' measurements.
"""

from typing import Any

import unrealsdk

from . import reads


class CampMap:
    """The camps by spawner name (spawners: name to weak pointer), and which camp each enemy came from (of: enemy name
    to camp name)."""

    def __init__(self) -> None:
        self.spawners: dict[str, Any] = {}
        self.of: dict[str, str] = {}

    def add(self, enemy: str, zone: Any) -> str | None:
        """Notes the camp owning that zone, read in this same sample (a seen.Seen's): says the camp's name, or None when
        the zone has no spawner."""
        try:
            spawner = zone.Outer
            component = getattr(spawner, "SpawnerComponent", None)
            name = reads.clean(spawner.Name)
        except Exception:
            return None
        if component is None:
            return None
        self.spawners.setdefault(name, unrealsdk.unreal.WeakPointer(spawner))
        self.of[enemy] = name
        return name

    def forget(self, name: str) -> None:
        """The camp no longer noted, until an enemy of it is noted again (add); its enemies keep their camp."""
        self.spawners.pop(name, None)

    def forget_enemy(self, enemy: str) -> None:
        """The enemy's camp no longer noted, once it has left the horde."""
        self.of.pop(enemy, None)
