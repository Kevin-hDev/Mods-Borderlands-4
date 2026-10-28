"""The menu: three lines, one per part of a grapple — the shot, the pull, and letting go — then the look.

One line per setting made Apex Movement's menu hard to follow (Kevin, 2026-09-17), so the settings
are grouped the way a grapple happens rather than the way the code is laid out. The look has its own line
(Kevin, 2026-10-14). A fifth line holds the hold mode, which the window shows with the keys.
"""

from mods_base import NestedOption

from . import control_menu, look_assets, look_choice, look_settings, settings, panel_preferences

shot = NestedOption(
    "shot_menu", [settings.grapple_range, settings.hook_speed, settings.stamina_cost, settings.melee_wins,
     settings.punch_range, settings.keep_game_grapple],
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

# The grapple gun's look and the switch that hides every look, on a page of their own (Kevin, 2026-10-14, sketch A,
# docs/apex_grapple/pistolet-grappin/apercus/2026-10-14-reglages/): "Show the rope" came from the shot's page.
look = NestedOption(
    "look_menu", [settings.show_rope, *look_settings.ALL],
    display_name="Look",
    description="What you see when you shoot: the gun, the rope and the hook.",
)

# Settings moved from one line to another, (option, former line, line now), so that each keeps its saved value
# (settings_moved.py).
MOVED = ((settings.show_rope, "shot_menu", "look_menu"),)

# A row that changes nothing greys and stays still, as Apex Heirloom's do (docs/mokup/menu_mods/decisions.md,
# 2026-09-26 and -29). By row: each tuple needs one of its switches on; every look row needs the rope shown.
DEPENDS_ON = {option.identifier: ((settings.show_rope.identifier,),) for option in look_settings.ALL}
def _ours(shown) -> bool:
    return shown.get(look_settings.look.identifier) == look_settings.GRAPPLE_GUN


# By row, a test of the window's values, saved or not: the grapple gun's rows change nothing with the classic look
# (spec-pistolet-grappin.md, section 9, choice 2); the glow's face nothing without the glow, the game's rope's colour
# nothing without the classic look (decisions.md, 14 October, « une page APPARENCE »).
ACTIVE_WHEN = {
    **{option.identifier: _ours for option in look_settings.OURS_ONLY},
    look_settings.glow_face.identifier: lambda shown: _ours(shown) and shown.get(
        look_settings.rope_look.identifier) in look_assets.ROPE["halo"]["looks"],
    look_settings.game_rope_colour.identifier: lambda shown: not _ours(shown),
}
# Rows whose choices show as two arrows around the chosen name: the colours, nine each, as sketch A has them.
ARROWS = frozenset({look_settings.rope_colour.identifier, look_settings.game_rope_colour.identifier})
# A page's sentence under its title, by page: the key of its text in panel_en.py, or a function that gives it, None
# while there is nothing to say. The LOOK page says why the grapple gun's look gave way to the classic one.
NOTICES = {"look": look_choice.notice}

# Key settings: the window shows them on its CONTROLS page, above the key choice (panel_pages.controls_page).
hold = NestedOption(
    "hold_menu", list(settings.HOLD),
    display_name="Hold to grapple",
    description="Hold the grapple key to grapple; a tap on the melee key still punches.",
)

MENU = [shot, pull, release, look, hold, control_menu.MENU, control_menu.RESTORE, control_menu.STORAGE,
        *panel_preferences.ALL]
