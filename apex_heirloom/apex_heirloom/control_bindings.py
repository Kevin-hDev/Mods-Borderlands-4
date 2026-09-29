"""Saves a key captured on the CONTROLS page to its device, with Apex Grapple's checks and messages.

The page is Grapple's (outils/sync_menu_heirloom.py); this is the service it calls, as Grapple's own control_bindings.py
is for the grapple. One key per device: a keyboard key or mouse button for the keyboard, a button for the controller.
"""

from typing import Any

INVALID = "Not saved. Choose a keyboard key, a mouse button or a controller button."
FAILED = "Could not save. Previous controls kept."
RESET = "Default controls restored."
RESERVED = "Not saved. Escape and console shortcuts are reserved. Previous controls kept."
# Grapple's reserved keys: Escape cancels a capture, Tilde opens the console.
RESERVED_KEYS = frozenset(("Escape", "Tilde"))


class Bindings:
    def __init__(self) -> None:
        # Import the running mod, not a second copy from source.
        from . import control_actions, control_config, mod
        self.actions, self.config, self.mod = control_actions, control_config, mod

    def ready(self) -> bool:
        return True

    def prepare(self) -> bool:
        # Nothing the mod does lasts: no put-away to stop before the keys change.
        return True

    def save(self, chosen: Any) -> tuple[bool, str]:
        from . import control_reserved, controller_option, report
        if not isinstance(chosen, tuple) or len(chosen) != 1 or type(chosen[0]) is not str:
            return False, INVALID
        key = chosen[0]
        if key in RESERVED_KEYS:
            return False, RESERVED
        try:
            reserved = control_reserved.console_keys()
        except Exception:
            # Do not save a key whose conflict with the console could not be checked.
            report.error_once("controls:console_keys", "console shortcuts unavailable; controls kept")
            return False, FAILED
        if key in reserved:
            return False, RESERVED
        device = next(item for item in self.config.DEVICES if item.name == self.config.device_of(key))
        try:
            value = controller_option.normalize_key(device.option, key)
        except ValueError:
            return False, INVALID
        if value is None:
            return False, INVALID
        if not self.actions.save_values(self.mod, ((device.option, value),)):
            return False, FAILED
        return True, f"Saved: {device.name} - {value}"

    def reset(self) -> tuple[bool, str]:
        values = tuple((option, option.default_value) for option in self.config.ALL)
        return (True, RESET) if self.actions.save_values(self.mod, values) else (False, FAILED)

    def summary(self) -> str:
        rows = []
        for device in self.config.DEVICES:
            selected = device.selection()
            rows.append(f"{device.name}: {selected[0] if selected else 'none'}")
        return "\n".join(rows)
