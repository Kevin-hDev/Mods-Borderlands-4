"""The slow walk key: while it walks, the auto sprint asks no sprint and the ground speed walks at the key's speed.

Kevin, 2026-09-25, from a keyboard player's Nexus comment: a movement key is down or up, so with the auto sprint every
push sprinted and the only way to walk was to aim or holster. Held rather than pressed once, as in Valorant (Kevin).
Caps Lock by default: the game gives it no action, and it reached a mod shortcut in game (Kevin, 2026-09-25). Not
Shift: a player who turns the auto sprint off sprints with it.

Toggle as a second choice, off by default (Kevin, 2026-09-25, from a Nexus comment asking for hold or toggle): held
stays the default so the published behaviour does not change under the players' feet.

A movement of its own, whatever the auto sprint does (Kevin, 2026-09-25, after the review of the toggle): a player
who sprints with the game's own key walks with this one all the same. The ground speed reads it directly, the auto
sprint refrains from sprinting while it walks, and slow_walk ends any other sprint (Kevin, 2026-09-26). The walk ends
with the character: after a death, a vehicle or a new game the player walks or sprints as usual, never comes back
walking slowly (Kevin, 2026-09-25). Full pack only: a separate file would show a slow walk that only half works.
"""

from typing import Any

from mods_base import BoolOption, SliderOption, keybind

from . import report
from .shortcut_key import KeyboardKeybindOption
from .speed_order import GAME_WALK

_walking = False


def _set_walking(wanted: bool) -> None:
    global _walking
    # Written only while the switch is on: off, nothing happens in game and a line would say otherwise (review).
    if wanted != _walking and switch.value is True:
        report.note(f"slow walk {'on' if wanted else 'off'}")
    _walking = wanted


def _on_key(event: Any) -> None:
    name = getattr(event, "name", str(event))
    # A mouse button pressed twice quickly comes as a double click, not a second press (audit, 2026-09-25).
    pressed = name in ("IE_Pressed", "IE_DoubleClick")
    if toggle.value is True:
        # The repeats of a key kept down would flip the walk back and forth: only a new press counts.
        if pressed:
            _set_walking(not _walking)
    elif pressed or name == "IE_Repeat":
        _set_walking(True)
    elif name == "IE_Released":
        _set_walking(False)


def _let_go(_option: Any, _value: Any) -> None:
    """A walk toggled on, then the mode or the switch changed: the release that would end it never comes."""
    _set_walking(False)


def _mode_changed(option: Any, value: Any) -> None:
    # Written at every change, the settings file's load included: a player's log then says which mode they play.
    report.note(f"slow walk mode {'toggle' if value is True else 'hold'}")
    _let_go(option, value)


# Named "Slow walk", never "Walk": the Movement page already has a walk speed, and two settings called walk that do
# different things confuse the player (Kevin, 2026-09-25). The identifiers stay: they are the players' settings files.
switch = BoolOption(
    "walk", True, display_name="Slow walk",
    description="Hold the key to walk slowly. With Slow walk toggle on, press it once instead.",
)
switch.on_change_anytime = _let_go
toggle = BoolOption(
    "walk_toggle", False, display_name="Slow walk toggle",
    description="Off: hold the key to walk slowly. On: press once to walk slowly, press again to stop.",
)
toggle.on_change_anytime = _mode_changed
bind = keybind(
    "walk_key", "CapsLock", _on_key,
    display_name="Slow walk key", description="Walk slowly: hold, or press once with Slow walk toggle on.",
    is_hidden=True, event_filter=None,
)
key = KeyboardKeybindOption.sole_entry(bind)
# Kevin, 2026-09-25: 300 by default, as Valorant, and no higher than the game's walk: the key only walks slower, the
# Movement page sets the faster speeds.
speed = SliderOption(
    "walk_key_speed", 300, 150, int(GAME_WALK), step=1, is_integer=True,
    display_name="Slow walk speed", description="Up to 540, the game's own walk.",
)


def walking() -> bool:
    return switch.value is True and _walking


def state_line() -> str:
    """Written once the mod is enabled: a settings file from before the toggle loads no mode line of its own."""
    mode = "toggle" if toggle.value is True else "hold"
    return f"slow walk {'on' if switch.value is True else 'off'} mode {mode} key {bind.key}"


def forget() -> None:
    """The character is gone, or the mod stops: a key held then would walk for ever once the mod is back."""
    _set_walking(False)
