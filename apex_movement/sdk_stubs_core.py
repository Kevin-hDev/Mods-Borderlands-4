"""Core option and value fakes shared by the Apex Movement tests."""

import enum
import types
from typing import Any

SLIDE_PATH = "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Slide.Move_Slide"
DASH_PATH = "/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/Move_Dash.Move_Dash"
CLIMB_ANIMATION_PATH = "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Wall_Climb_U.AS_Wall_Climb_U"


class FakeOption:
    def __init__(self, identifier: str, value: Any, *args: Any, **kwargs: Any) -> None:
        self.on_change_anytime = None
        # args holds a slider's bounds, in mods_base's order: min_value, max_value.
        self.identifier, self.value, self.args = identifier, value, args
        self.display_name = kwargs.get("display_name", identifier)
        # mods_base's names for a slider's bounds and first value; a switch has no bounds.
        self.min_value, self.max_value = (args + (None, None))[:2]
        self.default_value = value

    def __setattr__(self, name: str, value: Any) -> None:
        # Like mods_base: the change callback runs before a new value is stored, loading a settings file included.
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeKeybindOption(FakeOption):
    @classmethod
    def from_keybind(cls, bind: Any):
        option = cls(bind.identifier, bind.key, display_name=bind.display_name,
                     description=bind.description, is_rebindable=bind.is_rebindable)
        option.on_change_anytime = lambda _option, key: setattr(bind, "key", key)
        return option


class FakeNested:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        # As mods_base (options.py, BaseOption.__post_init__): copied once from the display name, never followed again.
        # The console menu draws it under the title whenever the two differ.
        self.description_title = kwargs.get("description_title") or self.display_name


class FakeHook:
    def __init__(self, fn: Any, path: str, identifier: str) -> None:
        self.fn, self.path, self.identifier, self.enabled = fn, path, identifier, False

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class FakeMod:
    """Behaves as mods_base.Mod does wherever the mod depends on it, down to the order of each step (mod.py:260-308).

    The fake used to skip the settings file, so no test ever saw a mod enabled from it while build_mod was still
    running — which is how a guard calling the module's own `mod` from on_enable shipped (review, 2026-09-18).
    """

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.kwargs, self.is_enabled = kwargs, False
        self.settings_file = types.SimpleNamespace(exists=lambda: state["settings_exists"])
        # What the settings file holds for "enabled" after the mod's last save; None while it never saved.
        self.saved_enabled: bool | None = None
        self.state = state
        for option in kwargs.get("options") or []:
            if hasattr(option, "children"):
                continue
            option.mod = self

    def save_settings(self) -> None:
        self.state["settings_saves"] += 1

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks") or []:
            hook.enable()
        for bind in self.kwargs.get("keybinds") or []:
            bind.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()
        self.saved_enabled = self.is_enabled

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks") or []:
            hook.disable()
        for bind in self.kwargs.get("keybinds") or []:
            bind.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()
        self.saved_enabled = False


def vector(x: float, y: float, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


class Mode:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<EMovementMode.{self.name}: 1>"


class Direction(enum.Enum):
    """Stands for the game's ERelativeDirectionType, with the values read in game."""

    ParentVelocity2D = 5
    ParentAimDirection2D = 18
