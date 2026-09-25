"""Controlled move, key and jump asset fakes for Apex Movement tests."""

import copy
import types
from typing import Any

from sdk_stubs_core import Direction

class FakeSlideAsset:
    """Move_Slide with its game values; its structs come back as copies, as the SDK may hand them out."""

    def __init__(self) -> None:
        self._speed = types.SimpleNamespace(constant=720.0)
        self._launch = types.SimpleNamespace(RelativeDirection=Direction.ParentAimDirection2D)
        self._steering = types.SimpleNamespace(constant=55.0)
        self._duration = types.SimpleNamespace(constant=1.35)
        self.bSpeedAffectedByMaxGroundSpeedScale = True
        self.bUseSlopeCurve = True
        # The curve read in game on 2026-09-16; its points are live views, as SDK arrays of structs are.
        self.SpeedScaleCurve = types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=[
            curve_key(0.0, 1.1017, 0.0, -0.2), curve_key(0.5675, 0.9728, -0.3, -0.3), curve_key(0.7437, 0.7737, -1.4, -1.4),
            curve_key(1.0, 0.3722, -2.0, 0.0),
        ]))
        self.SpeedSlopeScaleCurve = types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=[
            curve_key(-1.0, 0.5, 0.0, 0.5), curve_key(0.0, 1.0, 0.5, 1.4), curve_key(0.7, 2.0, 0.0, 0.0),
            curve_key(1.0, 2.0, 0.0, 0.0),
        ]))

    @property
    def speed(self) -> Any:
        return copy.copy(self._speed)

    @speed.setter
    def speed(self, value: Any) -> None:
        self._speed = copy.copy(value)

    @property
    def LaunchDirection(self) -> Any:
        return copy.copy(self._launch)

    @LaunchDirection.setter
    def LaunchDirection(self, value: Any) -> None:
        self._launch = copy.copy(value)

    @property
    def Duration(self) -> Any:
        return copy.copy(self._duration)

    @Duration.setter
    def Duration(self, value: Any) -> None:
        self._duration = copy.copy(value)

    @property
    def MoveLRRate(self) -> Any:
        return copy.copy(self._steering)

    @MoveLRRate.setter
    def MoveLRRate(self, value: Any) -> None:
        self._steering = copy.copy(value)


def curve_key(time: float, value: float, arrive: float = 0.0, leave: float = 0.0) -> Any:
    return types.SimpleNamespace(time=time, Value=value, ArriveTangent=arrive, LeaveTangent=leave)


class FakeDashAsset:
    """Move_Dash with the values read in game on 2026-09-16: Duration comes back as a copy, as the SDK may hand structs
    out; the curve points are live views, as SDK arrays of structs are, unless copy_keys makes them copies."""

    def __init__(self, copy_keys: bool = False, name: str = "Move_Dash") -> None:
        self.Name = name
        self._duration = types.SimpleNamespace(constant=0.33)
        self.speed = types.SimpleNamespace(constant=2500.0)
        self.copy_keys = copy_keys
        self._keys = [curve_key(0.0, 1.0), curve_key(0.15, 1.0, 0.0, -2.0), curve_key(0.17, 0.181, -2.0, 1.5),
                      curve_key(0.33, 0.48, 1.5, 0.0)]

    @property
    def Duration(self) -> Any:
        return copy.copy(self._duration)

    @Duration.setter
    def Duration(self, value: Any) -> None:
        self._duration = copy.copy(value)

    @property
    def SpeedScaleCurve(self) -> Any:
        keys = [copy.copy(key) for key in self._keys] if self.copy_keys else self._keys
        return types.SimpleNamespace(EditorCurveData=types.SimpleNamespace(keys=keys))


class FakeKeybind:
    """Stands in for mods_base.keybind: the tests fire key events by calling state["keybinds"][key]."""

    def __init__(self, state: dict, identifier: str, key: str, callback: Any, kwargs: dict) -> None:
        self.state, self.identifier, self._key, self.callback = state, identifier, key, callback
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_rebindable = kwargs.get("is_rebindable", True)
        self.is_hidden = kwargs.get("is_hidden", False)
        self.enabled = False

    @property
    def key(self) -> str:
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        if self.enabled:
            self.state["keybinds"].pop(self._key, None)
        self._key = value
        if self.enabled and value is not None:
            self.state["keybinds"][value] = self.callback

    def enable(self) -> None:
        self.enabled = True
        if self.key is not None:
            self.state["keybinds"][self.key] = self.callback

    def disable(self) -> None:
        self.state["keybinds"].pop(self.key, None)
        self.enabled = False


def mapping(action: str, key: str) -> Any:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action), Key=types.SimpleNamespace(KeyName=key))


class FakeJumpGoal:
    """A jump definition behind a kept pointer: shared, so every read sees every write."""

    def __init__(self, velocity: float, height: float, use_velocity: bool) -> None:
        self.InitialZVelocity, self.GoalHeight, self.bUseInitialZVelocity = velocity, height, use_velocity


def jump_goals() -> dict[str, Any]:
    """The five definitions with the values read in game on 2026-09-16."""
    return {
        "DefaultJump": FakeJumpGoal(840.0, 198.0, False),
        "SprintJump": FakeJumpGoal(735.0, 198.0, True),
        "DoubleJump": FakeJumpGoal(940.0, 225.0, True),
        "SlideJump": FakeJumpGoal(735.0, 190.0, True),
        "UpwardLadderJump": FakeJumpGoal(700.0, 175.0, True),
    }
