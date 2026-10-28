"""One character as the census read it: its actor, name, definition, zone and where things stood.

Valid for the read that made it only: game objects are not to be kept past it (the census's own rule,
docs/RUN/sondes/run_zone_pick.py). The census makes one for each enemy kept, the copies one for the zone of the camp
It Follows makes, whose zone is lent to the horde (docs/RUN/sondes/run_copies.py).
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Seen:
    actor: Any
    name: str
    definition: str
    # The enemy's own zone, None for one without a zone standing in the world (trial 6r); its path, "" then.
    zone: Any
    zone_path: str
    # Where the zone's centre and the actor stood, in cm, when read; the zone's combat radius in metres.
    centre: tuple | None
    radius_m: float
    at: tuple | None
    # Flyers never walk: the brain's walk is a walk on the ground (docs/RUN/sondes/run_chaser.py).
    walks: bool = True
    # Kept by a census that asked for the bosses (the normal mode's), without its zone.
    boss: bool = False
