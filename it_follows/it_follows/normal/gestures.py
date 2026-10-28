"""Which of an enemy's gestures the level speeds up (decisions 121 and 124): its blows, leaps and thrown weapons, never
its grenades nor the turrets it sets down (Kevin: « on le laisses comme les grenades pour les tourelles »), nor its
retreats (Kevin, 17 October 2026, of T_Cat_MeleeRetreat: « Le recul du chat conserve la meme vitesse de
deplacement »), nor its staggers, its turret's shots, its effects or its births.

An enemy's gestures are tricks of the game, each a script listed in TrickData.InstancedScripts while it runs, its name
saying what it is: TRAnim_Psycho_MeleeSwing_Script_Instanced_C, TLeap_Psycho_LeapAttack_…, TAnim_Psycho_RUpperThrow_…,
TRAnim_GunToter_Rifle_ThrowGrenade_… (trial 63, 72 tricks of 16 kinds of enemies, vérifié en jeu). They are no
montages: trial 62 read none in three minutes of fight. A dodge is not among them (none at trial 63).
"""

import re
from itertools import islice
from typing import Any

# The words of the gestures sped up and of those left to the game, in the scripts' names seen at trial 63; a name with
# none of them is left to the game.
SPED = re.compile(r"melee|leap|lunge|swing|bite|throw|spin", re.I)
LEFT = re.compile(r"grenade|turret|stagger|retreat", re.I)
# More scripts than trial 63 saw at once on one enemy (two).
MAX_SCRIPTS = 8


def sped(script: str) -> bool:
    """Whether a script's name is a gesture the level speeds up."""
    return SPED.search(script) is not None and LEFT.search(script) is None


def playing(pawn: Any) -> str | None:
    """The name of the first script running on the enemy that is a gesture sped up, else None."""
    for script in islice(pawn.TrickData.InstancedScripts, MAX_SCRIPTS):
        if script is None:
            continue
        name = str(script.Class.Name)
        if sped(name):
            return name
    return None
