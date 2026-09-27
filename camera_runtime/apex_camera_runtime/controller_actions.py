"""Expose validated player actions without owning controller lifecycle."""

from typing import Any

from . import active_mode, foot_preemption


class ControllerActions:
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
