"""Expose validated player actions without owning controller lifecycle."""

from typing import Any

from . import active_mode, foot_preemption
from .constants import CAMERA_TRANSITION, ORBIT_MODE, THIRD_PERSON_MODE


class ControllerActions:
    def set_desired_mode(self, mode: str, release_orbit: bool = True) -> None:
        if mode not in (THIRD_PERSON_MODE, ORBIT_MODE, CAMERA_TRANSITION):
            raise ValueError('unsupported foot camera mode')
        if mode == ORBIT_MODE or release_orbit:
            self._suspend('orbit', mode != THIRD_PERSON_MODE)
        self._desired_mode = mode

    def confirm_desired_mode(self) -> None:
        self._suspend('orbit', self._desired_mode != THIRD_PERSON_MODE)

    def presentation_mode(self):
        return self.orbit_aim.mode(self.climb.transition_mode(self))

    def shoulder_available(self) -> bool:
        return self.shoulder.available(self)

    def set_shoulder(self, settings: Any, left: bool) -> bool:
        if not self.shoulder_available():
            return False
        try:
            return self.shoulder.set(self.bridge, settings, left)
        except RuntimeError:
            self.stop()
            raise

    def toggle_shoulder(self, settings: Any) -> bool:
        try:
            left = settings.shoulder_left()
        except Exception:
            return False
        return self.set_shoulder(settings, not left)

    def orbit_available(self) -> bool:
        return active_mode.available(self)

    def set_orbit(self, settings: Any, enabled: bool, now_ns: int) -> bool:
        return self.foot_mode.set_orbit(self, settings, enabled, now_ns)

    def toggle_orbit(self, settings: Any, now_ns: int) -> bool:
        return self.foot_mode.toggle_orbit(self, settings, now_ns)

    def cancel_orbit(self, _settings: Any, now_ns: int) -> bool:
        return foot_preemption.cancel_choice(self.foot_mode, self, now_ns)

    def _request_transition(self, mode: str, call: Any) -> bool:
        return self.foot_mode.issue(call, mode, self.clock())
