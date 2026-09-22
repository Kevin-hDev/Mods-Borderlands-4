"""The menu: three lines, one per part of a grapple — the shot, the pull, and letting go.

One line per setting made Apex Movement's menu hard to follow (Kevin, 2026-09-17), so the settings
are grouped the way a grapple happens rather than the way the code is laid out.
"""

from mods_base import NestedOption

from . import control_menu, settings, panel_preferences

shot = NestedOption(
    "shot_menu", [settings.grapple_range, settings.hook_speed, settings.stamina_cost, settings.melee_wins,
     settings.punch_range, settings.keep_game_grapple, settings.show_rope],
    display_name="The shot",
    description="How far the hook reaches, how fast it flies, how much stamina it spends, when the key punches "
                "instead of grappling, and whether the game's own grapple points still work.",
)
pull = NestedOption(
    "pull_menu", [settings.pull_strength, settings.pull_speed_cap, settings.rope_carry,
                  settings.steer_strength, settings.steer_speed_cap],
    display_name="The pull",
    description="How hard the rope pulls, and how much the move stick bends the path. The stick is what draws the "
                "arc: hold it one way and turn the camera the other.",
)
release = NestedOption(
    "release_menu", [settings.release_on_key_up, settings.arrival_distance, settings.longest_pull,
                     settings.takeoff_lift, settings.ground_grace, settings.release_on_landing,
                     settings.block_jump],
    display_name="Letting go",
    description="What ends a pull. Whatever ends it, you keep the speed you reached.",
)

MENU = [shot, pull, release, control_menu.MENU, control_menu.RESTORE, control_menu.STORAGE,
        panel_preferences.language, panel_preferences.controller_icons, panel_preferences.last_page]
