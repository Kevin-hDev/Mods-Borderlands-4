"""The Hardcore's rule, one for both modes (decisions 89 and 109): the enemies 1 % tougher, and the player taking 1 %
more damage, every KILLS_PER_STEP kills, on top of the level or the BUFF. The normal mode counts its kills all game long
(normal/hardcore.py), the Horde those of each run (run_hardcore.py)."""

# Kevin: « 1% [...] tous les 100 kills ».
KILLS_PER_STEP = 100


def percent(kills: int) -> int:
    """The percent kills reach: a whole step each KILLS_PER_STEP."""
    return max(0, kills) // KILLS_PER_STEP


def factor(percent_reached: int) -> float:
    """What the enemies' health and the damage the player takes are multiplied by at that percent."""
    return 1.0 + percent_reached / 100.0
