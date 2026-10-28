"""Keybind fakes shared by Omni Sprint's source tests."""

from typing import Any


class FakeKeybind:
    def __init__(self, state: dict, identifier: str, key: str, callback: Any, kwargs: dict) -> None:
        self.state, self.identifier, self._key, self.callback = state, identifier, key, callback
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_rebindable = kwargs.get("is_rebindable", True)
        self.is_hidden = kwargs.get("is_hidden", False)
        self.enabled = False

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if self.enabled:
            self.state["keybinds"].pop(self._key, None)
        self._key = value
        if self.enabled and value is not None:
            self.state["keybinds"][value] = self.callback

    def enable(self):
        self.enabled = True
        if self.key is not None:
            self.state["keybinds"][self.key] = self.callback

    def disable(self):
        self.state["keybinds"].pop(self.key, None)
        self.enabled = False
