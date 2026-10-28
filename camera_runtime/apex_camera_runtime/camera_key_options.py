"""The camera's key options: a saved key cleaned on its way in, checked against the other camera keys when a menu
sets it, and read back from the saved file without that check (camera_commands.py judges the whole set)."""

from typing import TYPE_CHECKING, Any, Callable

from .key_option import (ControllerKeybindOption, KeyboardKeybindOption,
                         normalize_controller_key, normalize_keyboard_key)
from .keyboard_layout import TOP_ROW_SEVEN, TOP_ROW_SIX, key_at

if TYPE_CHECKING:
    from .camera_commands import CameraCommands


# A "Six" or "Seven" saved before the keyboard-named defaults (2026-10-07). On a keyboard whose 6 and 7 keys type
# something else (Hyphen and E_AccentGrave on AZERTY), no key press gives that name: it can only be the old default,
# which never fired there (Kevin, 2026-10-07: his Omni Sprint still had Six and Seven saved). It becomes the key's name.
UNREACHABLE = {old: new for old, new in (("Six", key_at(TOP_ROW_SIX, "Six")), ("Seven", key_at(TOP_ROW_SEVEN, "Seven")))
               if new != old}


def normalize_camera_key(value: Any) -> str | None:
    value = normalize_keyboard_key(value)
    return UNREACHABLE.get(value, value)


class _CameraOption:
    normalizer: Callable[[Any], str | None]

    def attach(self, commands: "CameraCommands") -> None:
        object.__setattr__(self, "_camera_commands", commands)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value":
            try:
                value = self.normalizer(value)
            except ValueError:
                value = None
            commands = getattr(self, "_camera_commands", None)
            if commands is not None and not commands.applying:
                try:
                    commands.validate({self.identifier: value})
                except ValueError:
                    return
        super().__setattr__(name, value)

    def _from_json(self, value: Any) -> None:
        """The SDK reads the saved keys one by one: judged then, a key was compared with the defaults of the keys not
        read yet, and a 7 saved for third person came back as P (Kevin, 2026-10-12). align() judges the whole set."""
        commands = getattr(self, "_camera_commands", None)
        if commands is None:
            super()._from_json(value)
            return
        commands.applying = True
        try:
            super()._from_json(value)
        finally:
            commands.applying = False


class CameraKeyboardOption(_CameraOption, KeyboardKeybindOption):
    normalizer = staticmethod(normalize_camera_key)


class CameraControllerOption(_CameraOption, ControllerKeybindOption):
    normalizer = staticmethod(normalize_controller_key)
