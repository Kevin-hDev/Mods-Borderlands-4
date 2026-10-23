"""A companion born AHEAD_CM in front of the hunter, facing him, of the companions' own camps.

The trials made a fresh spawner of their own for each companion (docs/renforts, trials 127 to 188: BL4 Arena's recipe,
verified in game for companions too). It Follows' camps (camps.py) follow the same recipe, verified in game for its
enemies, and hand a new character to a spawner once its own died, where the trials left one more spawner in the world
at each coming back (a spawner is never destroyed: destroying an actor we spawned crashed the game, 2026-10-05). The
companions keep camps of their own (a Camps of their own, MOST_CAMPS at most): a Horde camp is handed enemies, and a
companion's spawner must hold companions only, for its zone is how a companion just born is found (choose.py).
"""

import math
from typing import Any

AHEAD_CM = 300.0
# Eight companions, and as many on their way back whose spawners do not read their companion dead yet: a downed
# Decrepit Frame is hidden, then taken away, never read dead (trials 183 to 186).
MOST_CAMPS = 16


def ahead(player: Any, pc: Any) -> tuple[tuple[float, float, float], float]:
    """AHEAD_CM in front of the hunter where the camera looks, at his height, and that look's yaw."""
    yaw = float(pc.GetControlRotation().Yaw)
    here = player.K2_GetActorLocation()
    angle = math.radians(yaw)
    return (float(here.X) + math.cos(angle) * AHEAD_CM, float(here.Y) + math.sin(angle) * AHEAD_CM,
            float(here.Z)), yaw


class Births:
    """camps: an It Follows Camps of the companions' own (camps.Camps(report.announce, MOST_CAMPS))."""

    def __init__(self, camps: Any) -> None:
        self.camps = camps
        self.asked = 0

    def ask(self, definition: str, pc: Any) -> dict:
        """A companion of that definition asked in front of the hunter: asked, with the spawner's name, or why not.
        The camp chosen is a free one moved there, else a new one; its character comes a few seconds later. A failing
        call raises."""
        player = getattr(pc, "OakCharacter", None) if pc is not None else None
        if player is None:
            return {"done": "no_character"}
        kit = self.camps.kit()
        if isinstance(kit, str):
            return {"done": "no_kit", "why": kit}
        point, yaw = ahead(player, pc)
        survey = self.camps.survey()
        placed = self.camps.place(kit, survey.free, point, yaw + 180.0, player)
        if placed is None:
            return {"done": "no_camp"}
        camp, spawner = placed
        refused = self.camps.hand(kit, camp, spawner, definition)
        if refused is not None:
            return {"done": "refused", "why": refused}
        self.asked += 1
        return {"done": "asked", "spawner": camp.name}
