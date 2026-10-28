"""The automatic shoulder switch's options (shoulder_auto.py): on or off, and its two delays (Kevin, 2026-10-07).

On by default. The delays are the ones of his third trial (« ça fonctionne mieux là »): 0.15 s before switching away
from a wall, 0.30 s of clear view before coming back. Kevin wants players to set them.
"""

from mods_base import BoolOption, SliderOption

from . import option_texts
from .shoulder_auto import RETURN_S, SWAP_S, Values
from .speed_fov_options import bounded

MIN_SWAP_S, MAX_SWAP_S = 0.05, 1.00
MIN_RETURN_S, MAX_RETURN_S = 0.05, 3.00


class ShoulderAutoOptions:
    def __init__(self) -> None:
        self.switch = BoolOption("shoulder_auto", True, **option_texts.SHOULDER_AUTO)
        self.swap = SliderOption("shoulder_auto_swap", SWAP_S, MIN_SWAP_S, MAX_SWAP_S, step=0.05, is_integer=False,
                                 **option_texts.SHOULDER_AUTO_SWAP)
        self.back = SliderOption("shoulder_auto_return", RETURN_S, MIN_RETURN_S, MAX_RETURN_S, step=0.05,
                                 is_integer=False, **option_texts.SHOULDER_AUTO_RETURN)
        self.options = (self.switch, self.swap, self.back)

    def values(self) -> Values:
        """A hand-edited file falls back to the defaults."""
        return Values(self.switch.value is not False,
                      bounded(self.swap.value, MIN_SWAP_S, MAX_SWAP_S, SWAP_S),
                      bounded(self.back.value, MIN_RETURN_S, MAX_RETURN_S, RETURN_S))
