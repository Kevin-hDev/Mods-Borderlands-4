"""Option fakes shared by Omni Sprint's source tests: what the mod and its window read from mods_base's options."""

from typing import Any


class FakeOption:
    """As mods_base's BoolOption and SliderOption: an identifier, a value, its bounds and what the window shows."""

    def __init__(self, identifier: str, value: Any, min_value: Any = None, max_value: Any = None,
                 **kwargs: Any) -> None:
        self.identifier, self.value, self.default_value = identifier, value, value
        self.min_value, self.max_value, self.kwargs = min_value, max_value, kwargs
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.step = kwargs.get("step", 1)
        self.is_integer = kwargs.get("is_integer", True)
        self.is_hidden = kwargs.get("is_hidden", False)


class FakeKeybindOption(FakeOption):
    @classmethod
    def from_keybind(cls, bind: Any):
        option = cls(bind.identifier, bind.key, display_name=bind.display_name,
                     description=bind.description, is_rebindable=bind.is_rebindable)
        option.on_change_anytime = lambda _option, key: setattr(bind, "key", key)
        option.is_hidden = bind.is_hidden  # As mods_base: the option inherits the bind's visibility.
        return option

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


class FakeNestedOption:
    def __init__(self, identifier: str, children: list, **kwargs: Any) -> None:
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
