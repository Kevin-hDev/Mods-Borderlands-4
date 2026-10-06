"""Every setting of the mod, with its default and bounds (spec section 2, validated by Kevin on 2026-09-18, the 1.0.3
ones on 2026-10-03, the camera views on 2026-10-06).

Percentages of the game's own value, 100 being the game's, so that each effect turns off on its own: Kevin's rule for
Apex Movement, every movement can be turned off alone. The defaults are session 9's ("c'est nickel, on a ce qu'il
faut"). The grip has its own switch, since no percentage turns it off. The unlimited boost has its own switch too; the
push in the air adds to the game's, so 0 is the game's.
"""

import math

from mods_base import BoolOption, SliderOption, SpinnerOption

# Up to 300 (Kevin, 2026-09-19), once 250 typed past the old top of 200 had been driven with.
max_speed = SliderOption(
    "max_speed", 125, 100, 300, step=1, is_integer=True,
    display_name="Max speed",
    description="100% = the game's speed, boost included.",
)
acceleration = SliderOption(
    "acceleration", 250, 100, 500, step=1, is_integer=True,
    display_name="Acceleration",
    description="100% = the game's acceleration.",
)
turn_speed = SliderOption(
    "turn_speed", 250, 100, 500, step=1, is_integer=True,
    display_name="Turn speed",
    description="100% = game value.",
)
jump_height = SliderOption(
    "jump_height", 200, 100, 400, step=1, is_integer=True,
    display_name="Jump height",
    description="100% = game value.",
)
# Kevin, 2026-10-03, after session 12 drove it at 200: "200 par défaut et jusqu'à 300 max".
reverse_speed = SliderOption(
    "reverse_speed", 200, 100, 300, step=1, is_integer=True,
    display_name="Reverse speed",
    description="100% = the game's reverse speed.",
)
grip = BoolOption(
    "grip", True,
    display_name="Grip",
    description="The vehicle holds its line instead of sliding.",
)
turn_loss = SliderOption(
    "turn_loss", 9, 0, 30, step=1, is_integer=True,
    display_name="Speed lost in turns",
    description="Share of speed lost in a right-angle turn.",
)
# Kevin, 2026-10-03: "la durée est déjà pas mal par défaut, avec réglages jusqu'à 300 et illimité".
boost_duration = SliderOption(
    "boost_duration", 150, 100, 300, step=1, is_integer=True,
    display_name="Boost duration",
    description="100% = how long the game's boost lasts.",
)
# Off by default: Kevin's wish of 2026-10-02.
unlimited_boost = BoolOption(
    "unlimited_boost", False,
    display_name="Unlimited boost",
    description="The boost gauge never empties.",
)
# 100 = the boost's push on the ground; to be tuned in game (Kevin, 2026-10-03).
air_push = SliderOption(
    "air_push", 100, 0, 300, step=1, is_integer=True,
    display_name="Boost in the air",
    description="100% = the boost's ground push, in jumps and falls.",
)
# Kevin, 2026-10-03, after session 12's trial at 400: "200% avec réglage jusqu'à 500%".
toughness = SliderOption(
    "toughness", 200, 100, 500, step=1, is_integer=True,
    display_name="Toughness",
    description="200% = the vehicle takes half the damage.",
)
# Kevin, 2026-10-03, after session 12's trial at 500: "300% ... jusqu'à 500%".
weapon_damage = SliderOption(
    "weapon_damage", 300, 100, 500, step=1, is_integer=True,
    display_name="Weapon damage",
    description="100% = the game's damage, machine gun and rockets.",
)
OPTIONS = [max_speed, acceleration, turn_speed, jump_height, reverse_speed, grip, turn_loss, boost_duration,
           unlimited_boost, air_push, toughness, weapon_damage]
# The setting each lever of levers.py multiplies, by the name the levers give.
FACTORS = {"max_speed": max_speed, "acceleration": acceleration, "turn_speed": turn_speed, "jump_height": jump_height,
           "reverse_speed": reverse_speed, "weapon_damage": weapon_damage}

# The camera views at the wheel, in the order the view key goes through them (spec section 3.8, Kevin, 2026-10-06).
VIEWS = ("Far", "Default", "Close", "Closer", "Closest", "Custom")
DEFAULT_VIEW = "Default"
CUSTOM_VIEW = "Custom"
# Each fixed view's camera distance to the top of the driver, in share of the game's. Far, Close and Closer are trial
# 4's (docs/investigations/vehicle_driving/camera/2026-10-06-distance-camera-vehicule.md, Kevin: "c'est parfait");
# Closest was added after it, one more step of about 0.7.
VIEW_SHARES = {"Far": 1.35, "Close": 0.7, "Closer": 0.5, "Closest": 0.35}
vehicle_view = SpinnerOption(
    "vehicle_view", DEFAULT_VIEW, list(VIEWS), wrap_enabled=True,
    display_name="Vehicle view",
    description="The camera view at the wheel.",
)
# In game units, 1 = 1 cm: the game's camera sits about 650 from the top of the driver (trial 4).
custom_forward = SliderOption(
    "custom_forward", 0, -500, 500, step=10, is_integer=True,
    display_name="Custom forward/back",
    description="Custom view: camera forward (+) or back (-).",
)
custom_side = SliderOption(
    "custom_side", 0, -300, 300, step=10, is_integer=True,
    display_name="Custom left/right",
    description="Custom view: camera right (+) or left (-).",
)
custom_height = SliderOption(
    "custom_height", 0, -300, 300, step=10, is_integer=True,
    display_name="Custom up/down",
    description="Custom view: camera up (+) or down (-).",
)
CUSTOM = [custom_forward, custom_side, custom_height]
CAMERA_OPTIONS = [vehicle_view, *CUSTOM]


def keep_in_bounds() -> list[str]:
    """Brings every slider back within its bounds, and a value that is not a number back to its default.

    Neither the console menu nor the settings file holds a slider to its bounds: 250 typed for Max speed, shown
    [100-200], was taken and driven with (2026-09-19). Run before the values are read, so none outside reaches the game.
    """
    told: list[str] = []
    for option in (*OPTIONS, *CUSTOM):
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
    """Each lever's factor, by the name levers.py gives its setting. The duration and the toughness divide: a gauge
    that lasts 1.5 times longer empties 1.5 times slower, and a vehicle twice as tough takes half the damage."""
    made = {name: option.value / 100.0 for name, option in FACTORS.items()}
    made["boost_cost"] = 0.0 if unlimited_boost.value else 100.0 / boost_duration.value
    made["damage_taken"] = 100.0 / toughness.value
    return made


def push_strength() -> float:
    """The push in the air as a share of the boost's push on the ground (spec section 3.6)."""
    return air_push.value / 100.0


def loss_per_degree() -> float:
    """The share of speed lost for each degree the grip turns, so that a 90 degree turn loses turn_loss percent."""
    return 1.0 - (1.0 - turn_loss.value / 100.0) ** (1.0 / 90.0)


def current_view() -> str:
    """The view to show at the wheel; a name the settings file does not know is the game's own."""
    return vehicle_view.value if vehicle_view.value in VIEWS else DEFAULT_VIEW


def next_view(view: str) -> str:
    """The view the key goes to after this one; after the last comes the first."""
    index = VIEWS.index(view) if view in VIEWS else VIEWS.index(DEFAULT_VIEW)
    return VIEWS[(index + 1) % len(VIEWS)]


def custom_offset() -> tuple[float, float, float]:
    """The Custom view's offset in the camera's axes: forward, right, up."""
    return float(custom_forward.value), float(custom_side.value), float(custom_height.value)
