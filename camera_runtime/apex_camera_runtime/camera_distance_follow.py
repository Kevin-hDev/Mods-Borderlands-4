"""Each frame, the automatic camera distance (camera_distance_auto.py) reads the room the camera guard measured
(camera_distance_room.py) and tells the camera offset whether to show the close distance."""

from typing import Any

from .camera_distance import CLOSE, SECONDS
from .camera_distance_auto import GLIDE_S, AutoDistance, cramped
from .easing import MAX_STEP_S


def _room(reading) -> str:
    return f"ceiling {reading.ceiling:.0f} cm, narrowest {reading.narrowest:.0f} cm"


class CameraDistanceFollow:
    def __init__(self) -> None:
        self.auto = AutoDistance()
        self.reset()

    def reset(self) -> None:
        self.auto.reset()
        self.last_ns: int | None = None
        # Seconds left of an automatic glide: the distance eases at GLIDE_S meanwhile, at the key's pace otherwise.
        self.gliding_s = 0.0

    @property
    def glide_s(self) -> float:
        return GLIDE_S if self.gliding_s > 0.0 else SECONDS

    def player_key(self) -> None:
        self.auto.player_key()
        self.gliding_s = 0.0

    def close(self, controller: Any, chosen: object, aiming: bool, now_ns: int, enabled: bool = True) -> bool:
        """Whether the close distance stands in for the chosen one this frame; switched off in the menu, never, and a
        close distance shown glides back."""
        seconds = 0.0 if self.last_ns is None else min(max((now_ns - self.last_ns) / 1e9, 0.0), MAX_STEP_S)
        self.last_ns = now_ns
        self.gliding_s = max(self.gliding_s - seconds, 0.0)
        if not enabled:
            if self.auto.close:
                self.gliding_s = GLIDE_S
                controller.log("automatic distance: switched off, chosen distance back")
            self.auto.reset()
            return False
        room = getattr(getattr(controller.bridge, "collision", None), "room", None)
        reading = room.take() if room is not None else None
        was = self.auto.close
        squeezed = None if reading is None else cramped(reading, self.auto.holding)
        shown = self.auto.step(squeezed, chosen != CLOSE and not aiming, seconds)
        if shown is not was:
            self.gliding_s = GLIDE_S
            controller.log(f"automatic distance: {'close' if shown else 'chosen distance back'} ({_room(reading)})")
        return shown
