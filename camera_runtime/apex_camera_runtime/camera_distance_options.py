"""The camera distance's options (camera_distance.py): the key's saved choice, hidden, and the close and far distances
the player sets on the CAMERA VIEW page.

Kevin, 2026-10-07: « il faut qu'on puisse le régler manuellement au détail près ». In metres to the centimetre, as the
page shows them; normal stays the game's camera. The two ranges stay on their side of normal, so close is always
closer than normal and far always farther.
"""

from mods_base import SliderOption

from . import option_texts
from .camera_distance import CLOSE, DISTANCES, FAR, NORMAL, NORMAL_CM, valid
from .speed_fov_options import bounded

MIN_CLOSE_M, MAX_CLOSE_M = 1.00, 2.50
MIN_FAR_M, MAX_FAR_M = 2.60, 6.00
CLOSE_M, FAR_M = DISTANCES[CLOSE] / 100, DISTANCES[FAR] / 100


class CameraDistanceOptions:
    def __init__(self) -> None:
        self.option = SliderOption("camera_distance", NORMAL, 0, len(DISTANCES) - 1, step=1, is_integer=True,
                                   is_hidden=True, **option_texts.CAMERA_DISTANCE)
        self.close = SliderOption("camera_distance_close", CLOSE_M, MIN_CLOSE_M, MAX_CLOSE_M, step=0.01,
                                  is_integer=False, **option_texts.CAMERA_DISTANCE_CLOSE)
        self.far = SliderOption("camera_distance_far", FAR_M, MIN_FAR_M, MAX_FAR_M, step=0.01, is_integer=False,
                                **option_texts.CAMERA_DISTANCE_FAR)
        self.options = (self.close, self.far)

    def index(self) -> int:
        value = self.option.value
        return value if valid(value) else NORMAL

    def distances(self) -> tuple[float, float, float]:
        """Close, normal and far in centimetres; a hand-edited file falls back to the defaults."""
        return (bounded(self.close.value, MIN_CLOSE_M, MAX_CLOSE_M, CLOSE_M) * 100, NORMAL_CM,
                bounded(self.far.value, MIN_FAR_M, MAX_FAR_M, FAR_M) * 100)

    def save(self, value: int) -> None:
        if not valid(value):
            raise ValueError("invalid camera distance")
        previous = self.option.value
        self.option.value = value
        try:
            self.option.mod.save_settings()
        except Exception:
            self.option.value = previous
            raise
