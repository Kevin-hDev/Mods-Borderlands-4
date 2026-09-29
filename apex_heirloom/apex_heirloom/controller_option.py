"""The holster's device-aware check, built on the generated shared key options.

The keyboard adds the holster's wheel rule; controller validation stays in key_option.py, copied from the camera runtime.
"""

from typing import Any

from .keyboard_option import normalize_put_away_key
from .key_option import ControllerKeybindOption, normalize_controller_key


def normalize_key(option: Any, value: Any) -> str | None:
    """The window's check before it saves a key: a controller button for the controller, a key otherwise."""
    if isinstance(option, ControllerKeybindOption):
        return normalize_controller_key(value)
    return normalize_put_away_key(value)
