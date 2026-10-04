"""Vehicle settings grouped for both the SDK menu and the shared window."""

from mods_base import NestedOption
from .vehicle_unlock_runtime import runtime

from . import settings

# Keep the original option objects: the driving loop and saved settings use them.
driving = NestedOption(
    "driving_menu",
    [settings.max_speed, settings.acceleration, settings.turn_speed, settings.jump_height, settings.reverse_speed],
    display_name="Driving", description="Vehicle speed, reverse, turning and jumps.",
)
handling = NestedOption(
    "handling_menu", [settings.grip, settings.turn_loss],
    display_name="Handling", description="Control how the vehicle holds a turn.",
)
boost = NestedOption(
    "boost_menu", [settings.boost_duration, settings.unlimited_boost, settings.air_push],
    display_name="Boost", description="How long the boost lasts and how it pushes in the air.",
)
combat = NestedOption(
    "combat_menu", [settings.toughness, settings.weapon_damage],
    display_name="Combat", description="Vehicle toughness and weapon damage.",
)

vehicles = runtime.menu.option(NestedOption)
ALL = MENU = [driving, handling, boost, combat, vehicles]
