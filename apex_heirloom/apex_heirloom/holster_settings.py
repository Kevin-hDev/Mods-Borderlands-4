"""What the player sets for the holster, Tidy Weapons' part of the mod: whether its keys put the weapon away, whether
each key is held or pressed, and how long a hold lasts.

Each choice is a switch, On to hold (Kevin, 2026-09-25, choosing between two sketches of the window: the menus'
On/Off switch, or two Press / Hold buttons). The step-1 spinners, keyboard_mode and controller_mode, left with it: an
older settings file loads without them, and both keys hold by default as they did. The part's own switch came when
Tidy Weapons joined the heirloom (Kevin, 2026-09-26: « un interrupteur par partie »): a player may keep the heirloom
and put the weapon away with another mod.
"""

from mods_base import BoolOption, SliderOption

from .key_press import HOLD, PRESS
from .slider_values import bounded

KEYBOARD, CONTROLLER = "keyboard", "controller"

holster = BoolOption(
    "holster", True, display_name="Holster",
    description="No: your keys no longer put your weapon away.",
)
# Held by default on both (Kevin, 2026-09-25: "maintient A", "maintient carré pour ranger l'arme"). One short sentence
# each, as every menu description (Kevin, 2026-09-23).
keyboard_hold = BoolOption(
    "keyboard_hold", True, display_name="Keyboard: Hold",
    description="Hold the key rather than press it once.",
)
controller_hold = BoolOption(
    "controller_hold", True, display_name="Controller: Hold",
    description="Hold the button, as Square also reloads on one press.",
)
# Not under 0.2 s: the game reloads on a tap released within its tap time, 0.2 s by default in Unreal (inferred, the
# game's list does not print it). A shorter hold would put the weapon away during a reload tap, and reload with it.
# 0.4 s by default, among the game's own holds (0.2 to 0.5 s, releves/apex_inputs_2026-09-16.log).
hold_time = SliderOption(
    "hold_time", 0.4, 0.2, 1.0, step=0.05, is_integer=False, display_name="Hold Time",
    description="How long to hold the key or button, in seconds.",
)
# The window's HOLSTER page shows these, the switch first; the keys themselves are chosen on its CONTROLS page
# (control_config.py).
ALL = (holster, keyboard_hold, controller_hold, hold_time)
_SWITCHES = {KEYBOARD: keyboard_hold, CONTROLLER: controller_hold}


def mode(device: str) -> str:
    # Only an explicit Off presses: a malformed saved value keeps the hold, which never fires on a reload tap.
    return PRESS if _SWITCHES[device].value is False else HOLD


def hold_seconds() -> float:
    # At 0 a reload tap would put the weapon away too: the slider's bounds hold whatever the settings file says.
    return bounded(hold_time)
