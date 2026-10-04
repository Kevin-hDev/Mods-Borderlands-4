"""Extend the existing Movement SDK fake with the menu option fields it now reads."""

import sdk_stubs
from types import SimpleNamespace


def install() -> None:
    sdk_stubs.install()
    # install() replaces the module; retrieve the current fake before patching it.
    import sys
    options = sys.modules["mods_base"]
    fake = sdk_stubs.FakeOption
    original = fake.__init__

    def initialize(self, identifier, value, *args, **kwargs):
        original(self, identifier, value, *args, **kwargs)
        self.step = kwargs.get("step", 1)
        self.is_integer = kwargs.get("is_integer", True)
        self.description = kwargs.get("description", "")
        self.true_text = kwargs.get("true_text")
        self.false_text = kwargs.get("false_text")

    fake.__init__ = initialize
    options.SpinnerOption = fake


class Widget:
    """Stateful UMG boundary for form polling; not an in-game rendering proof."""
    def __init__(self):
        self.checked = False
        self.value = 0.0
        self.active = 0
        self.selecting = False
        self.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="None"))

    def IsChecked(self):
        return self.checked

    def SetIsChecked(self, value):
        self.checked = value

    def SetValue(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def SetActiveWidgetIndex(self, value):
        self.active = value

    def SetIsEnabled(self, value):
        self.enabled = value

    def SetRenderOpacity(self, value):
        self.opacity = value

    def SetText(self, value):
        self.text = value

    def SetVisibility(self, value):
        self.visibility = value

    def SetBrush(self, value):
        self.brush = value

    def SetNoKeySpecifiedText(self, value):
        self.empty_text = value

    def SetKeySelectionText(self, value):
        self.selection_text = value

    def SetSelectedKey(self, value):
        self.SelectedKey = value

    def GetIsSelectingKey(self):
        return self.selecting
