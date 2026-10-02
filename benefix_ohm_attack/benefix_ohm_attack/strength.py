"""How hard the beam hits: a damage per second that grows with the player's level, as a weapon's does.

The game hands the target exactly the amount it is given, then applies the element's own bonus itself (in game,
2026-10-01: 2 250 asked, 2 250 lost; fire on flesh, 1.2 times). So the whole strength is this module's.

The growth is the game's own balance scalar, 1.09 a level (universal_balance_scalar, read in the game's files on
2026-09-30; its use as "9 % a level" is a reading, not verified in game).
"""

GROWTH_PER_LEVEL = 1.09
MAX_LEVEL = 200


def per_second(at_level_one: float, level: int) -> float:
    """The damage dealt in one second of beam on a target, at that level."""
    steps = max(1, min(int(level), MAX_LEVEL)) - 1
    return max(0.0, float(at_level_one)) * GROWTH_PER_LEVEL ** steps


def per_hit(at_level_one: float, level: int, hits_per_second: float) -> float:
    """One hit's share of a second of beam."""
    return per_second(at_level_one, level) / max(1.0, float(hits_per_second))
