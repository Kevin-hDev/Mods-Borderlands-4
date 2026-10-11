"""The framing by action and the camera motion on foot, summed into one camera offset per frame."""

from dataclasses import replace

from . import action_framing, camera_distance
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
        self.distance = Easing(1, REST)
        self.motion = Motion()
        self._last_ns: int | None = None

    def step(self, values: tuple[float, float], sample: Sample | None, pitch: float, yaw: float,
             now_ns: int, distance: float = 0.0, glide_s: float = camera_distance.SECONDS) -> tuple | None:
        """values: the framing's and the motion's strength (0 when off); distance: the chosen camera distance's
        forward offset (camera_distance.py), eased over glide_s. The offset (forward, right, up), or None once all rest
        at nothing, so the camera is left to the game."""
        framing_strength, motion_strength = values
        # The camera's places follow the held aim button: they come back while the game zooms out, in one move with
        # it. Waiting for the zoom-out to end made a second move after it (Kevin, 2026-10-11, close and far distances).
        sample = None if sample is None else replace(sample, aiming=sample.aim_held)
        # Aiming keeps the game's aim camera, as the framing does, but from the close distance: brought back there,
        # the camera no longer came forward and the aim's zoom looked like a stretched picture (Kevin, 2026-10-11).
        goal = (max(distance, 0.0) if action_framing.action(sample) == "aim" else distance,)
        if self._last_ns is None:
            # Entering third person puts the camera at its distance at once; only a key press glides.
            self.distance.snap(goal)
        step_s = 0.0 if self._last_ns is None else min(max((now_ns - self._last_ns) / 1e9, 0.0), MAX_STEP_S)
        self._last_ns = now_ns
        x, z = self.framing.step(action_framing.target(sample, framing_strength), action_framing.seconds(sample),
                                 step_s)
        (chosen,) = self.distance.step(goal, glide_s, step_s)
        motion = self.motion.step(motion_strength, sample, pitch, yaw, step_s)
        offset = (x + chosen + motion[0], motion[1], z + motion[2])
        return None if offset == ZERO else offset
