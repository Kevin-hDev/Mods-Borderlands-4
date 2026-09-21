"""Bridge to the installed mod: one settings authority, no replacement gameplay code."""

INVALID = "Not saved. Choose valid keys from the same device."
FAILED = "Could not save. Previous controls kept."
DISABLED = "Apex Grapple is disabled."
RESET = "Default grapple controls restored."
RESERVED = "Not saved. Escape and console shortcuts are reserved. Previous controls kept."


class Bindings:
    def __init__(self):
        # Import the running mod, not a second copy from source.
        from . import control_actions, control_config, mod
        self.actions, self.config, self.mod = control_actions, control_config, mod

    def ready(self):
        return bool(self.mod.is_enabled)

    def prepare(self):
        from . import frame, session
        return self.ready() and session.reset(frame.rope)

    def save(self, chosen):
        if not self.ready():
            return False, DISABLED
        config = self.config
        valid = config.catalogue()
        if (not isinstance(chosen, tuple) or len(chosen) not in (1, 2)
                or any(type(key) is not str or key not in valid for key in chosen)):
            return False, INVALID
        if any(key in config.RESERVED_KEYS for key in chosen):
            return False, RESERVED
        from . import control_reserved, report
        try:
            reserved = control_reserved.console_keys()
        except Exception:
            # Do not save a key whose conflict with the console could not be checked.
            report.error_once("controls:console_keys", "console shortcuts unavailable; controls kept")
            return False, FAILED
        if any(key in reserved for key in chosen):
            return False, RESERVED
        device = next(item for item in config.DEVICES if item.name == config.device_of(chosen[0]))
        if any(config.device_of(key) != device.name for key in chosen):
            return False, INVALID
        if len(chosen) == 2 and (chosen[0] == chosen[1] or any(key in config.PULSE_KEYS for key in chosen)):
            return False, INVALID
        if not self.actions.assign(self.mod, device, chosen):
            return False, FAILED
        return True, f"Saved: {config.DEVICE_NAMES[device.name]} - {' + '.join(chosen)}"

    def reset(self):
        if not self.ready():
            return False, DISABLED
        values = tuple((option, option.default_value) for option in self.config.ALL)
        return (True, RESET) if self.actions.save_values(self.mod, values) else (False, FAILED)

    def summary(self):
        rows = []
        for device in self.config.DEVICES:
            selected = device.selection()
            label = ' + '.join(selected) if selected else self.config.GAME
            rows.append(f"{self.config.DEVICE_NAMES[device.name]}: {label}")
        return '\n'.join(rows)
