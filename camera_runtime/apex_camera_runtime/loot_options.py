"""Shared option definitions; each elected mod saves its own player choice."""
import math
from mods_base import BoolOption, SliderOption
from .loot_constants import (BASE_DISTANCE, DEFAULT_MULTIPLIER, MIN_MULTIPLIER,
                             MAX_MULTIPLIER, MULTIPLIER_STEP)


class LootOptions:
    def __init__(self):
        self.enabled = BoolOption(
            'extended_loot', True, display_name='Extended Loot Reach',
            description='Pick up loot and open containers from farther away.')
        self.multiplier = SliderOption(
            'loot_reach', DEFAULT_MULTIPLIER, MIN_MULTIPLIER, MAX_MULTIPLIER,
            step=MULTIPLIER_STEP, is_integer=False, display_name='Loot Reach',
            description="1: the game's reach; 2: twice as far.")
        self.options = [self.enabled, self.multiplier]

    def distance(self):
        value = self.multiplier.value
        if (self.enabled.value is not True or isinstance(value, bool)
                or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not MIN_MULTIPLIER <= value <= MAX_MULTIPLIER):
            return 0.0
        return BASE_DISTANCE * float(value)
