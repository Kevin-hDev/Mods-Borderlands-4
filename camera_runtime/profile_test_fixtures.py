"""Shared by the camera profile tests: a stand-in for the SDK's mods_base, installed before the runtime's modules are
imported, and a profile's values built from the defaults."""

import pathlib
import sys
import types
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


class Option:
    def __init__(self, identifier, value=None, min_value=None, max_value=None, *args, **kwargs):
        self.identifier, self.value, self.kwargs = identifier, value, kwargs
        self.min_value, self.max_value = min_value, max_value


class KeybindOption:
    pass


if "mods_base" not in sys.modules:
    mods_base = types.ModuleType("mods_base")
    mods_base.SliderOption = mods_base.BoolOption = Option
    mods_base.KeybindOption = KeybindOption
    sys.modules["mods_base"] = mods_base

from apex_camera_runtime import profile_values  # noqa: E402


def values(**changes) -> profile_values.Values:
    return replace(profile_values.DEFAULTS, **changes)
