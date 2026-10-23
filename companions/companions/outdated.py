"""It Follows 1.0.10 and before carry their own companions' team, under it_follows.companions, and never join the
team's owners (characters/companions/owners.py): beside one, Companions would make a second team follow the hunter.
Found by that team's module, which the game loads with It Follows whether it is on or off, at the game's launch:
Companions then starts no team and asks to update It Follows (plan-companions.md, step 3). An It Follows that carries
the characters' package keeps its team under it_follows.characters and joins the owners instead.
"""

import sys

OLD_TEAM = "it_follows.companions.team"


def old_it_follows() -> bool:
    return OLD_TEAM in sys.modules
