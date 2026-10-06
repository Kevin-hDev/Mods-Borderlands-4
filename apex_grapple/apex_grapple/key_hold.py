"""Hold mode: the grapple key grapples once held for the hold time, and a tap on the melee key still punches.

Kevin, 2026-10-06, from a player's request on Nexus ("hold r3 for x amount should be grapple. Tap r3 should just be
melee"), added beside the other controls rather than replacing them: one switch per device, off by default
(settings.py). The press is kept from the game at once, since the game would act on it; the mod decides at the release
or at the hold time, whichever comes first. Released before, the press gives the game back the action its key carries
(melee_press.py): the melee key punches as before, a key of the player's own does nothing (Kevin, same day). Held
through, it fires the rope; a shot the rope refuses (an enemy in punch range, a game interaction, nothing in range)
gives the game its action too, as a refused press does in the normal mode.

A mouse wheel notch has no release, so it always fires at once. One press is held at a time, and it is forgotten with
the rest of the input at every session reset.
"""

from typing import Any

from . import control_config, melee_press, report, settings

NS_PER_S = 1_000_000_000
_SWITCHES = {control_config.KEYBOARD: settings.keyboard_hold, control_config.GAMEPAD: settings.controller_hold}

_key: str | None = None
_pressed_ns = 0
_native = False


def wanted(key: str) -> bool:
    """A press on this key waits for the hold time; a malformed switch keeps the press at once, as before the mode."""
    return key not in control_config.PULSE_KEYS and _SWITCHES[control_config.device_of(key)].value is True


def start(key: str, now_ns: int, native: bool) -> None:
    global _key, _pressed_ns, _native
    _key, _pressed_ns, _native = key, now_ns, native


def pending() -> bool:
    return _key is not None


def released() -> None:
    """The key came up before the hold time: the game gets its tap back."""
    key, native = _key, _native
    forget()
    if key is not None and native:
        report.note(f"tap on {key}: gave the game {', '.join(melee_press.press(key)) or 'nothing'}")


def tick(rope: Any, character: Any, now_ns: int) -> None:
    """Fires a press held for the hold time. Read after the frame's settings check, so the time is a valid one."""
    if _key is None:
        return
    if wanted(_key) and now_ns - _pressed_ns < float(settings.hold_time.value) * NS_PER_S:
        return
    key, pressed_ns, native = _key, _pressed_ns, _native
    forget()
    if rope.fire(character, now_ns, native_action=native, held=True):
        report.note(f"held {key} {(now_ns - pressed_ns) / NS_PER_S:.2f}s: grapple key taken")
    elif native:
        report.note(f"held {key}, no grapple: gave the game {', '.join(melee_press.press(key)) or 'nothing'}")


def forget() -> None:
    global _key, _pressed_ns, _native
    _key, _pressed_ns, _native = None, 0, False
