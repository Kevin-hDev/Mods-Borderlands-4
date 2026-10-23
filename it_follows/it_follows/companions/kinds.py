"""The companions a team is made of: the only place that names them (docs/renforts/sondes/companions.py points here).

The allies are real characters of the game, not Lemmy dressed (decision 20 of docs/renforts/README.md), among the 44
the game hands out to spawn that are not enemies, each seen in game by Kevin (trial 162). Ten were chosen, four remain:
Supervisor, Skank Eyes and the Badass Domination Engine follow but never fight (trial 163, decision 25); the Sloshed
Psycho turns on the other companions (trial 171, decision 34); the armed Frame holds no health the game keeps (trial
174, decision 41); the Badass Pangolin is never hit (trials 171, 175 and 176, decision 45). The name is the one the game
shows in English.

The six hunters are Lemmy dressed (decision 18): one definition, a look each (hunters.py), so a companion is known
by its name, never its definition. Lemmy, a gunner of Rush's hub, fights (trial 134); dressed, he followed and fought
in It Follows' team (trial 189).
"""

from typing import NamedTuple

from . import hunters

LEMMY = "Char_GunToter_Shatter2_Lemmy"


class Kind(NamedTuple):
    definition: str
    name: str
    # The hunter's look Lemmy wears (hunters.py); None for an ally, born as itself.
    look: str | None = None


ALLIES = (
    Kind("Char_TedioreFrame_NoVacancy_Side", "Decrepit Frame"),
    Kind("Char_GunToter_SiblingRivalry_Crankus", "Crankus"),
    Kind("Char_MeleeFish_NPC", "Brine Type M"),
    Kind("Char_NPC_Abomination", "Abomination"),
)
HUNTERS = tuple(Kind(LEMMY, look.name, look.name) for look in hunters.LOOKS)
ALL = HUNTERS + ALLIES
BY_NAME = {kind.name: kind for kind in ALL}
