"""The five levels of It Follows (decisions 47 and 70): the player picks one, and it sets the rest. The sixth, 120, is
gone (Kevin, 14 October 2026, after trial 15): the horde now holds 120 enemies at most (decision 69), all of which
would have had to stand within 50 m of the hunter.

Each level holds the number of enemies the wave aims at within 50 m of the hunter and its band (decision 39: 90 to
105 % of the target, Kevin's example for 100; at level 25, 22.5 and 26.25 rounded inwards), and the catch-up's
distances: an enemy left behind is placed behind_m behind the hunter (Kevin, 14 October 2026: « 30 m ce sera pour les
niveaux 80/100/120, 25 on sera sur 40, 40/60 on sera sur 35 ») and brought back once farther than far_m, behind_m
plus 20 m as in the trials (placed at 30 m, brought back beyond 50 m), so that the five enemies of one second, placed
4 m apart, never land already too far. Each level spreads the distances at which its enemies are put behind the
hunter, born again or brought back (decision 66, spread.py). The copies at the start, the wave's growth and the spread
are the same at every level until each level is tuned in game (spec, section 4, step 5). Only level 40 has been
verified in game (trial 8e).
"""

from dataclasses import dataclass

# (share in percent, metres added to the distance): Kevin, 14 October 2026, after trial 14: « exemple 60% des
# ennemies pop a la distance actuel, 20% pop 10m plus loin, 10% 15m plus loin et 10% 5m plus proche ».
SPREAD = ((60, 0.0), (20, 10.0), (10, 15.0), (10, -5.0))


@dataclass(frozen=True)
class Level:
    target: int
    low: int
    high: int
    behind_m: float
    far_m: float
    spread: tuple = SPREAD


LEVELS = {
    25: Level(25, 23, 26, 40.0, 60.0),
    40: Level(40, 36, 42, 35.0, 55.0),
    60: Level(60, 54, 63, 35.0, 55.0),
    80: Level(80, 72, 84, 30.0, 50.0),
    100: Level(100, 90, 105, 30.0, 50.0),
}
# The one level verified in game; the menu's own default is chosen with its drawing (spec, section 4, step 3).
DEFAULT = 40


def level(target: int) -> Level:
    """The level of that target, the default one for a value the settings file holds that is no level."""
    return LEVELS.get(target, LEVELS[DEFAULT])
