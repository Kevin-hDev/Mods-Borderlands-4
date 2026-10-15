"""What a character is, by its definition's name: an enemy, a boss, or other (a player, an NPC, one who fights
nobody), and whether it walks. None for a definition the game's catalogue does not resolve: the census passes it over
as an unknown kind, as the trials did (docs/RUN/sondes/run_zone_pick.py).

The table is made offline from the enemy research's catalogue (kinds_data.py, written by
docs/RUN/outils/kinds_export.py), so that the mod reads no file at run time.
"""

from .kinds_data import KINDS

ENEMY, BOSS, OTHER = "enemy", "boss", "other"


def kind(name: str | None) -> tuple[str, bool] | None:
    """(enemy, boss or other, whether it walks) for a definition's name, whatever its case; None when unknown."""
    if not name:
        return None
    return KINDS.get(name.lower())
