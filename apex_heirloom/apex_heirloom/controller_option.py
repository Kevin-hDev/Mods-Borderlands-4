"""The keys' device-aware check, built on the generated shared key options.

The keyboard adds the wheel rule (keyboard_option.py); controller validation stays in key_option.py, copied from the
camera runtime.
"""

from typing import Any

from .keyboard_option import normalize_wheel_free_key
from .key_option import ControllerKeybindOption, normalize_controller_key


def normalize_key(option: Any, value: Any) -> str | None:
    """The window's check before it saves a key: a controller button for the controller, a key otherwise."""
    if isinstance(option, ControllerKeybindOption):
        return normalize_controller_key(value)
    return normalize_wheel_free_key(value)
