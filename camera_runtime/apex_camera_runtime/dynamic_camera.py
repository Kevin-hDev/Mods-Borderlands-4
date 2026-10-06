"""The framing by action and the camera motion on foot, summed into one camera offset per frame."""

from . import action_framing
from .camera_motion import Motion
from .easing import MAX_STEP_S, Easing
from .player_sample import Sample

REST = 0.01
ZERO = (0.0, 0.0, 0.0)


class DynamicCamera:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.framing = Easing(2, REST)
        self.motion = Motion()
        self._last_ns: int | None = None

    def step(self, values: tuple[float, float], sample: Sample | None, pitch: float, yaw: float,
             now_ns: int) -> tuple | None:
        """values: the framing's and the motion's strength (0 when off). The offset (forward, right, up), or None
        once both rest at nothing, so the camera is left to the game."""
        framing_strength, motion_strength = values
        step_s = 0.0 if self._last_ns is None else min(max((now_ns - self._last_ns) / 1e9, 0.0), MAX_STEP_S)
        self._last_ns = now_ns
        x, z = self.framing.step(action_framing.target(sample, framing_strength), action_framing.seconds(sample),
                                 step_s)
        motion = self.motion.step(motion_strength, sample, pitch, yaw, step_s)
        offset = (x + motion[0], motion[1], z + motion[2])
        return None if offset == ZERO else offset
