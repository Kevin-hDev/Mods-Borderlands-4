"""The shoulder key and the menu's shoulder choice, accepted from the elected owner only."""

from typing import Any


def toggle(runtime: Any, owner: str) -> bool:
    client = runtime.arbiter.active()
    if client is None or client.owner != owner:
        return False
    try:
        left = client.settings.shoulder_left()
        # During an automatic swap the key brings the chosen shoulder back (shoulder_auto.py).
        if runtime.third_person is not None and runtime.third_person.undo_auto_shoulder(client.settings):
            return True
    except Exception:
        return False
    return choose(runtime, owner, not left)


def choose(runtime: Any, owner: str, left: bool) -> bool:
    client = runtime.arbiter.active()
    if (type(left) is not bool or client is None or client.owner != owner
            or runtime.third_person is None):
        return False
    try:
        if (not client.settings.third_person_enabled()
                or not runtime.third_person.shoulder_available()):
            return False
        return bool(runtime.third_person.set_shoulder(client.settings, left))
    except Exception:
        client.settings.note("shoulder shortcut: setting could not be saved")
        return False
