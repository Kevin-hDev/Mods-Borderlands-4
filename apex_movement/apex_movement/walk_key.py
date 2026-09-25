"""The walk key: while it is held, the auto sprint asks no sprint and the ground speed walks at the key's speed.

Kevin, 2026-09-25, from a keyboard player's Nexus comment: a movement key is down or up, so with the auto sprint every
push sprinted and the only way to walk was to aim or holster. Held rather than pressed once, as in Valorant (Kevin).
Caps Lock by default: the game gives it no action, and it reached a mod shortcut in game (Kevin, 2026-09-25). Not
Shift: a player who turns the auto sprint off sprints with it.

Shared rather than the auto sprint's own: the ground speed, another movement, reads the walk the auto sprint asks.
"""

from typing import Any

from mods_base import BoolOption, SliderOption, keybind

from .shortcut_key import KeyboardKeybindOption
from .speed_order import GAME_WALK

_held = False
_asked = False


def _on_key(event: Any) -> None:
    global _held
    name = getattr(event, "name", str(event))
    # A mouse button pressed twice quickly comes as a double click, not a second press (audit, 2026-09-25).
    if name in ("IE_Pressed", "IE_Repeat", "IE_DoubleClick"):
        _held = True
    elif name == "IE_Released":
        _held = False


switch = BoolOption(
    "walk", True, display_name="Walk key",
    description="Hold the key to walk instead of sprinting.",
)
bind = keybind(
    "walk_key", "CapsLock", _on_key,
    display_name="Walk key", description="Hold to walk instead of sprinting.",
    is_hidden=True, event_filter=None,
)
key = KeyboardKeybindOption.sole_entry(bind)
# Kevin, 2026-09-25: 300 by default, as Valorant, and no higher than the game's walk: the key only walks slower, the
# Movement page sets the faster speeds.
speed = SliderOption(
    "walk_key_speed", 300, 150, int(GAME_WALK), step=1, is_integer=True,
    display_name="Walk key speed", description="Up to 540, the game's own walk.",
)


def held() -> bool:
    return switch.value is True and _held


def ask(wanted: bool) -> None:
    global _asked
    _asked = wanted


def asked() -> bool:
    return _asked


def forget() -> None:
    """A disabled bind never hears the release: a key held then would walk for ever once the mod is back."""
    global _held, _asked
    _held = _asked = False
