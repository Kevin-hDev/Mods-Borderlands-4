"""The key chosen for each device, as Apex Grapple's CONTROLS page reads them: one key per device, never a chord.

Grapple's page shows each device's selection and saves a captured key to the device it belongs to. Here a device is
one of the two keys' options (keys.py), which stay the one authority on the keys.
"""

from typing import Any

from . import holster_settings, keys, pack

KEYBOARD, GAMEPAD = "keyboard", "gamepad"


def device_of(key: str) -> str:
    return GAMEPAD if key.startswith("Gamepad_") else KEYBOARD


class Device:
    def __init__(self, name: str, option: Any) -> None:
        self.name, self.option = name, option

    def selection(self) -> tuple[str, ...] | None:
        key = self.option.value
        return (key,) if key else None


DEVICES = (Device(KEYBOARD, keys.keyboard_key), Device(GAMEPAD, keys.controller_key))
# The keys the window saves, restores and undoes: none in a file without the holster (pack.py), which has no key.
ALL = tuple(device.option for device in DEVICES) if pack.runs(holster_settings.holster.identifier) else ()
