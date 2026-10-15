"""The normal mode's three levels (decisions 80 and 85, Kevin, 15 October 2026), set in advance and never tuned in
game: every value of a level is here and nowhere else.

camps: how many times their enemies the game's camps hold (camps_grown.py). chase_m: the combat radius each enemy's
own zone is widened to (Kevin: « 250m c'est pas long, poursuite on peu pousser a 350m pour bandit/senior »); Predator
is the same mode with a longer chase, never the Horde's hunt (Kevin, after trying it: « on veut la meme chose que les
deux autres mais que les ennemies suivent plus longtemps c'est tout »), at the Horde's 600 m, the radius with which a
Psycho followed much farther from its home (decision 33, verified in game). speed: the enemies' own speed bonus times
this.
dodge_speed: their own time during a dodge times this (×2, ×3 and ×4 seen and kept at trial 21). dodge_chance: the
chance of each dodge, every condition open (dodge_rate.py), and dodge_moving: IsMovingSpeed times this, the two Kevin
kept after trials 26 and 27 (« bandit c'est bon comme ca, seniors je dirais peux reduire a 90% [...] predator reduire
a peut etre 80% »; « oui c'est bon comme ca on valide »). health and taken: the enemies' health, shield and armour, and
the damage the player takes, times these: the normal mode's own BUFF, BUFF+ and BUFF++, not the Horde's; Predator's
health doubled after trial 30 (Kevin: « la vie en predator on va passer de 80 a 100% ce sera mieux »).

Rebalanced after trial 34 (Kevin, 15 October 2026: « On va re modifier quelques stats »): health +45, +75 and +130 %,
dodges ×1.7, ×2.3 and ×2.8 faster, dodge chance 35, 45 and 55 %, Predator's damage taken +30 %. Predator dodged less
than Senior (trial 27: some 23 dodges a minute against 42), a mistake of figures (Kevin: « j'ai du me tromper de
chiffre »); its chance is now the highest, IsMovingSpeed ×100 kept.

Faster after trial 35 (decision 100, Kevin, 15 October 2026: « c'est pas assez je le sent pas du tout en jeu »): speed
×1.2, ×1.5 and ×1.7 in place of ×1.1, ×1.2 and ×1.4.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    name: str
    camps: float
    chase_m: float
    speed: float
    dodge_speed: float
    dodge_chance: float
    dodge_moving: float
    health: float
    taken: float


LEVELS = {
    "Bandit": Level("Bandit", 1.5, 350.0, 1.2, 1.7, 0.35, 1.0, 1.45, 1.1),
    "Senior": Level("Senior", 2.0, 350.0, 1.5, 2.3, 0.45, 1.0, 1.75, 1.2),
    "Predator": Level("Predator", 2.0, 600.0, 1.7, 2.8, 0.55, 100.0, 2.3, 1.3),
}
# The mildest at first: the mode is there to play the game, and the player raises it at will (Claude's choice).
DEFAULT = "Bandit"
# Every level (decision 85): the rest after a dodge and the warmup before the first of a fight divided by this, as in
# trials 25 to 27.
DODGE_REST_DIVIDE = 20.0


def level(name: object) -> Level:
    """The level of that name, the default one for a value the settings file holds that is no level."""
    return LEVELS.get(str(name), LEVELS[DEFAULT])
