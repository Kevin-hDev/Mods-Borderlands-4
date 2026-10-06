"""One saved Orbit distance per mod; only the elected camera applies it."""

from mods_base import SliderOption

from . import option_texts
from .orbit_zoom_values import (DISTANCE_STEP, MAX_DISTANCE, MIN_DISTANCE,
                               NATIVE_DISTANCE, valid_distance)


class OrbitZoomOptions:
    def __init__(self) -> None:
        self.option = SliderOption(
            "orbit_distance", NATIVE_DISTANCE, MIN_DISTANCE, MAX_DISTANCE,
            step=DISTANCE_STEP, is_integer=True, is_hidden=True, **option_texts.ORBIT_DISTANCE)

    def distance(self) -> float:
        value = self.option.value
        return float(value) if valid_distance(value) else float(NATIVE_DISTANCE)

    def save(self, value: float) -> None:
        if not valid_distance(value):
            raise ValueError("invalid orbit distance")
        previous = self.option.value
        self.option.value = value
        try:
            self.option.mod.save_settings()
        except Exception:
            self.option.value = previous
            raise
