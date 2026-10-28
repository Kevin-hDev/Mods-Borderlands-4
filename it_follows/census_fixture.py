"""Fake characters and combat zones for the census and recruiter tests, as the census reads them
(it_follows/reads.py): a character's definition, death, place and zone; a zone's place, radius and path.

The definitions are names of It Follows' own kinds table (it_follows/kinds_data.py), so that the census is tested
with the table the mod ships rather than a fake one.
"""

import math
import types
from typing import Any

from sdk_stubs import FakeGbxDefPtr, FakePawn, FakeStruct, vector

WORLD = "/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel"
# Where the game keeps a world event's zones (docs/RUN/enquetes/2026-10-10-recensement.md).
EVENTS = "/Temp/Game/Maps/WorldStamps/Layouts/Events/DynamicEvents/Camp"
PSYCHO = "Char_PsychoBasic_Male"
CAT = "Char_CatAdult"
YOUNG_CAT = "Char_CatYoung"
BAT = "Char_BatBasic"
BOSS = "Char_Cat_Mine_Boss_CityCat"
NPC = "Char_InfantryAR_MissionNPC"
UNKNOWN = "Char_NoSuchThing"


class Zone:
    """A combat zone: its centre on the X axis, its radius in centimetres (None: unreadable), its path."""

    def __init__(self, x: float, name: str, radius_cm: float | None = 3000.0, folder: str = WORLD) -> None:
        self.x, self.path = x, f"{folder}.{name}.Territory"
        if radius_cm is not None:
            self.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=radius_cm))

    def _path_name(self) -> str:
        return self.path

    def K2_GetComponentLocation(self) -> Any:
        return vector(self.x, 0.0, 0.0)


def enemy(name: str, x: float | None, definition: Any, zone: Any, is_dead: Any = False) -> FakePawn:
    """A character on the X axis, at a place that is not finite when x is None. definition: its name, None for a
    character without actor data, an Exception raised when read. zone: what GetTerritory gives, an Exception raised.
    is_dead: what the game says, None for a character without a health state. asks counts the zone asked."""
    fields: dict = {}
    if definition is not None:
        held = definition if isinstance(definition, Exception) else FakeGbxDefPtr(definition)
        fields["GbxActorData"] = FakeStruct({"GbxActorDef": held})
    if is_dead is not None:
        fields["HealthState"] = types.SimpleNamespace(bCurrentlyDead=is_dead)
    pawn = FakePawn(name, vector(math.nan if x is None else x, 0.0, 0.0), fields=fields)
    pawn.asks = 0

    def get_territory() -> Any:
        pawn.asks += 1
        if isinstance(zone, Exception):
            raise zone
        return zone

    pawn.GetTerritory = get_territory
    return pawn
