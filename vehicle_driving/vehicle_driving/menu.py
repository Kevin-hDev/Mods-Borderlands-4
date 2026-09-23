"""Vehicle settings grouped for both the SDK menu and the shared window."""

from mods_base import NestedOption

from . import settings

# Keep the original option objects: the driving loop and saved settings use them.
driving = NestedOption(
    "driving_menu", [settings.max_speed, settings.acceleration, settings.turn_speed, settings.jump_height],
    display_name="Driving", description="Vehicle speed, turning and jumps.",
)
handling = NestedOption(
    "handling_menu", [settings.grip, settings.turn_loss],
    display_name="Handling", description="Control how the vehicle holds a turn.",
)

ALL = MENU = [driving, handling]
