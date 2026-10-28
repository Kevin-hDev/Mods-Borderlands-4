"""What happens when the player chooses: the mode, the heirloom, a skin or the glow's force. Each applies from the
next weapon change (Kevin, 2026-09-26, docs/mokup/menu_mods/decisions.md): a new list goes to empty hands at once and
the game reads it then; a new heirloom's model, skin and hold go on the heirloom in hand at once, hidden until the
arms play its animations; a new skin or force is seen at once on the heirloom in hand.

Why, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 19): Kevin chose that the menu offers the knife and the
axe, each with its animations, skins and glow (sketch H2). The window sets their options; each option's change comes
here (__init__.py).
"""

import functools
from typing import Any, Callable

from unrealsdk import logging

from . import heirloom, heirloom_settings


def _in_hand() -> Any:
    """The heirloom in hand, unless it is on its way out after a switch-off."""
    component = heirloom.held()
    return component if component is not None and not heirloom.STATE.retiring else None


def _now(option: Any, value: Any) -> None:
    """The option takes `value` before its change runs: mods_base calls the change first and sets the value after,
    its guard making this set a plain one; what follows reads the options as the player chose them."""
    option.value = value


def _guarded(change: Callable[[Any, Any], None]) -> Callable[[Any, Any], None]:
    """An option's change that never raises: mods_base would leave its guard on the option, and none of the
    option's later changes would run for the session. The failure goes to the log; the choice is kept and worn the
    next time the heirloom is built."""
    @functools.wraps(change)
    def run(option: Any, value: Any) -> None:
        try:
            change(option, value)
        except Exception as error:
            logging.error(f"{heirloom.PREFIX} {option.identifier} {value!r}: its change failed, {error!r}")
    return run


def mode_chosen(value: str) -> None:
    """The menu's mode is about to become `value`: its list goes to empty hands, played from the next weapon change."""
    if _in_hand() is not None:
        heirloom.give_list(heirloom_settings.chosen_mode(value))


@_guarded
def mode_changed(_option: Any, value: Any) -> None:
    mode_chosen(value)


@_guarded
def heirloom_changed(option: Any, value: Any) -> None:
    """Another heirloom chosen, in the skin it last wore: its list goes to empty hands, played from the next weapon
    change, and its model and hold go on the heirloom in hand, hidden until then."""
    _now(option, value)
    heirloom.say(f"heirloom chosen: {heirloom_settings.chosen_heirloom()}")
    component = _in_hand()
    if component is not None and heirloom.give_list():
        heirloom.rewear(component)


@_guarded
def skin_changed(option: Any, value: Any) -> None:
    """A heirloom's skin chosen: on the heirloom in hand at once, when it is that heirloom."""
    _now(option, value)
    component = _in_hand()
    if component is not None and option is heirloom_settings.SKINS[heirloom_settings.chosen_heirloom()]:
        heirloom.dress(component)


@_guarded
def glow_changed(option: Any, value: Any) -> None:
    """The glow's force chosen: on the heirloom in hand at once."""
    _now(option, value)
    component = _in_hand()
    if component is not None:
        heirloom.dress(component)
