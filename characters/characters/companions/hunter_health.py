"""Reinforcements, trial 172: the hunter's most health, which the companions' is sized on (decision 35).

The game keeps a player's health in its resource pool Health, whose maximum the attribute health_resource_max_value
reads (the game's decoded attributes: a PropertyValueResolver of MaxValue on resource'Health'; his base is
calc_playerhealth_base, PlayerHealthBase times universal_balance_scalar to the power of his level, in
docs/candidats/editeur_de_sauvegarde/releves/2026-10-01-niveau-max-suite/archives/decoded/). Read by the game's
attribute reader, GetValueOfAttribute(name, actor, default), the call It Follows' health_pools.py makes on enemies
(verified in game). Never read on the hunter before trial 172.
"""

import math
from typing import Any

import unrealsdk

ATTRIBUTE = "health_resource_max_value"
LIBRARY = "GbxAttributeBlueprintLibrary"
# What the reader gives back when the attribute is not there.
DEFAULT = -1.0


def most(pc: Any) -> Any:
    """The hunter's most health, a float above zero; else why, as text."""
    try:
        character = pc.OakCharacter
        value = float(unrealsdk.find_class(LIBRARY).ClassDefaultObject.GetValueOfAttribute(ATTRIBUTE, character,
                                                                                           DEFAULT))
    except Exception as error:
        return f"unread:{type(error).__name__}"
    return value if math.isfinite(value) and value > 0.0 else f"unread:{value}"
