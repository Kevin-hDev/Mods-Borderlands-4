"""Checked SDK signatures and ownership of the binding window's update hook."""

from itertools import islice

import unrealsdk

from . import control_window_clock

PREFIX = "[MovementUIWindow]"
MAX_PARAMS = 16


def note(message):
    unrealsdk.logging.info(f"{PREFIX} {message}")


def require_signature(cls, method, expected):
    fields = tuple(islice(cls._find(method)._properties(), MAX_PARAMS + 1))
    names = tuple(str(field.Name) for field in fields)
    note(f"signature={method} params={','.join(names)}")
    if names != expected:
        raise ValueError("Unsupported interface signature")


def install_listener(callback):
    installed = control_window_clock.shared().start(__package__, callback)
    note(f"pause_timer_installed={installed}")
    return installed


def remove_listener():
    control_window_clock.shared().stop(__package__)
