"""Extend the existing Movement SDK fake with the menu option fields it now reads."""

import sdk_stubs


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

    fake.__init__ = initialize
    options.SpinnerOption = fake
