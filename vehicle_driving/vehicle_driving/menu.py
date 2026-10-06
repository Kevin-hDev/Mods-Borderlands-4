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
# The view and the Custom view's sliders; the window puts the view key's card under them (Kevin, 2026-10-06, spec
# section 2).
camera = NestedOption(
    "camera_menu", settings.CAMERA_OPTIONS,
    display_name="Camera", description="The camera view at the wheel, and where the Custom view sits.",
)

vehicles = runtime.menu.option(NestedOption)
# CAMERA after VEHICLES: the window reopens on the page saved by its rank (panel_preferences.last_page), and a player
# whose last page was VEHICLES must find it again, as Save Editor appends its WEAPONS page (2026-10-06).
ALL = MENU = [driving, handling, boost, combat, vehicles, camera]
# The choices the window shows with two arrows around the chosen name (panel_choices.py): six names do not fit on one
# line of buttons.
ARROWS = frozenset((settings.vehicle_view.identifier,))
