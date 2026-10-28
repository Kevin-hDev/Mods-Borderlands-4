"""The timing of the heirloom's draw and put-away (apex_draw.py, apex_put_away.py). The player sets the draw's start
and speed in the menu (settings.py); the rest stays as Kevin set it.

The draw's defaults are Kevin's, set in game on 2026-09-25 ("c'est très bien"). The put-away's, its own speed and a
0.25 s rise, were kept by Kevin the same day: "c'est parfait comme ça, tout s'enchaîne proprement".
"""

from dataclasses import dataclass

# The draw lasts 0.67 s: a start later than this would leave no rise to see. Slower than half speed or faster than
# three times, a move is a typo; a rise longer than 0.6 s would outlast the game's own draw.
LIMITS = {"start": (0.0, 0.6), "speed": (0.5, 3.0), "away": (0.5, 3.0), "rise": (0.05, 0.6)}


@dataclass
class Timing:
    start: float = 0.4
    speed: float = 0.8
    away: float = 1.0
    rise: float = 0.25
