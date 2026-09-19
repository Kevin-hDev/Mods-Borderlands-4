"""Every setting of the mod, with its default and bounds (spec section 2, validated by Kevin on 2026-09-18).

Percentages of the game's own value, 100 being the game's, so that each effect turns off on its own: Kevin's rule for
Apex Movement, every movement can be turned off alone. The defaults are session 9's ("c'est nickel, on a ce qu'il
faut"). The grip has its own switch, since no percentage turns it off.
"""

import math

from mods_base import BoolOption, SliderOption

# Up to 300 (Kevin, 2026-09-19), once 250 typed past the old top of 200 had been driven with.
max_speed = SliderOption(
    "max_speed", 125, 100, 300, step=1, is_integer=True,
    display_name="Max speed",
    description="Top speed in percent of the game's, Hover Drive bonus included. 100 is the game's own.",
)
acceleration = SliderOption(
    "acceleration", 250, 100, 500, step=1, is_integer=True,
    display_name="Acceleration",
    description="How fast the vehicle picks up speed, after a turn too, in percent of the game's. "
                "100 is the game's own.",
)
turn_speed = SliderOption(
    "turn_speed", 250, 100, 500, step=1, is_integer=True,
    display_name="Turn speed",
    description="How fast the vehicle turns toward your camera, in percent of the game's. 100 is the game's own.",
)
jump_height = SliderOption(
    "jump_height", 200, 100, 400, step=1, is_integer=True,
    display_name="Jump height",
    description="How high the vehicle jumps, in percent of the game's. 100 is the game's own.",
)
grip = BoolOption(
    "grip", True,
    display_name="Grip",
    description="The vehicle goes where it faces instead of sliding on in turns. Turned off, it slides as in the "
                "game.",
)
# "degree" in words: the menu was never seen drawing a degree sign, and a missing glyph would show as a box.
turn_loss = SliderOption(
    "turn_loss", 9, 0, 30, step=1, is_integer=True,
    display_name="Speed lost in a 90 degree turn",
    description="The share of speed the grip lets go in a 90 degree turn. The game's own braking adds to it, so a "
                "turn at full throttle loses a little more.",
)
OPTIONS = [max_speed, acceleration, turn_speed, jump_height, grip, turn_loss]
# The setting each lever of levers.py multiplies, by the name the levers give.
FACTORS = {"max_speed": max_speed, "acceleration": acceleration, "turn_speed": turn_speed, "jump_height": jump_height}


def keep_in_bounds() -> list[str]:
    """Brings every slider back within its bounds, and a value that is not a number back to its default.

    Neither the console menu nor the settings file holds a slider to its bounds: 250 typed for Max speed, shown
    [100-200], was taken and driven with (2026-09-19). Run before the values are read, so none outside reaches the game.
    """
    told: list[str] = []
    for option in OPTIONS:
        if getattr(option, "min_value", None) is None:
            continue
        value = float(option.value)
        kept = min(option.max_value, max(option.min_value, value)) if math.isfinite(value) else option.default_value
        if kept != value:
            told.append(f"setting {option.identifier}={option.value} outside {option.min_value}-{option.max_value}, "
                        f"set to {kept}")
            option.value = kept
    return told


def factors() -> dict[str, float]:
    return {name: option.value / 100.0 for name, option in FACTORS.items()}


def loss_per_degree() -> float:
    """The share of speed lost for each degree the grip turns, so that a 90 degree turn loses turn_loss percent."""
    return 1.0 - (1.0 - turn_loss.value / 100.0) ** (1.0 / 90.0)
