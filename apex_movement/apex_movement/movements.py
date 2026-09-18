"""Which modules and which menu lines make up each movement, so a movement can be turned off or shipped on its own.

Kevin's rule, 2026-09-18: one mod is one movement. Two movements were sharing a module without anyone seeing it — the
ground speeds rode on the auto sprint's switch, so turning the auto sprint off quietly gave the game's own speeds
back. Nothing in the code stated the rule, so nothing caught the breach; it was found twice, both times by accident.

This file states it. test_movement_rules.py checks the code against it, and the separate file per movement
(conception, decision 2) is built from it. Every exception carries its reason here, so none can be added in silence.
"""

from dataclasses import dataclass

# Read by every movement and owned by none: the game's fields, the settings, the frame loop, the menu.
# speed_order ties sliders of several movements together on purpose (design decision 9), and every file needs it.
SHARED = ("__init__", "family", "frame", "game", "menu", "movements", "ownership", "pack", "report", "settings",
          "speed_order")

# Settings any movement may read: LONGEST_SLIDE_S is read by the slides and by the landing slide's safety net,
# which belong to two movements. The speeds every movement reads come from speed_order, not from settings.
SHARED_SETTINGS = ("LONGEST_SLIDE_S",)


@dataclass(frozen=True)
class Movement:
    name: str
    modules: tuple[str, ...]
    menu_groups: tuple[str, ...]
    # The separate file this movement ships as: the package name inside it, and the name it wears in the mod list.
    # None of them is "apex_movement", which belongs to the full pack: two files sharing a package name would fight
    # over the same import, and only one would load.
    file: str = ""
    mod_name: str = ""
    # Why it cannot be switched off. Empty means it has a switch, which is what the rule expects.
    always_on_because: str = ""
    # Why one switch carries two movements. Empty means it carries exactly one, which is what the rule expects.
    one_switch_because: str = ""
    # Why it takes more than one menu line. Empty means it takes exactly one, which is what the rule expects.
    two_lines_because: str = ""


MOVEMENTS = (
    Movement("Movement", ("ground_speed",), ("movement_menu",), "apex_speed", "Apex Speed",
             always_on_because="a walking speed has no off state; the game's own values are named in the sliders, so "
                               "a player who wants them back types them in"),
    Movement("Auto sprint", ("sprint",), ("auto_sprint_menu",), "apex_auto_sprint", "Apex Auto Sprint"),
    Movement("Slides", ("slide", "slide_physics", "slide_direction", "slide_steering", "axle_slide"),
             ("slides_menu", "axle_slide_menu"), "apex_slides", "Apex Slides",
             two_lines_because="the Axle slide is a slide, and the one exception Kevin named to one movement per mod "
                               "(2026-09-18): it keeps its own line because it is off by default and has five "
                               "settings of its own"),
    Movement("Dash", ("dash",), ("dash_menu",), "apex_dash", "Apex Dash"),
    Movement("Ground slam and landing slide", ("air_crouch", "air_actions", "air_bindings", "air_keys"),
             ("air_crouch_menu",), "apex_ground_slam", "Apex Ground Slam",
             one_switch_because="both need the crouch key blocked, and that block is what removes the game's own slam "
                                "on a held crouch; two switches would allow a state where the block stays on while "
                                "the player asked for neither, losing them the held-crouch slam with no way to tell "
                                "why (Kevin, 2026-09-18)"),
    Movement("Air / tap strafe", ("air_strafe",), ("air_strafe_menu",), "apex_air_strafe", "Apex Air Strafe"),
    # jump_report writes the jumps this movement shapes: under its switch it runs in one installed file, not in each.
    Movement("Heavier fall", ("heavier_fall", "jump_goals", "jump_report"), ("heavier_fall_menu",),
             "apex_heavier_fall", "Apex Heavier Fall"),
    Movement("Wall climb", ("wall_climb", "wall_sense", "climb_aim", "wall_choice", "climb_rules", "climb_refusal",
                            "climb_animation", "jump_press", "air_jumps", "move_watch"), ("wall_climb_menu",),
             "apex_wall_climb", "Apex Wall Climb"),
)


def owner(module: str) -> Movement | None:
    """The movement a module belongs to, or None when it is shared."""
    for movement in MOVEMENTS:
        if module in movement.modules:
            return movement
    return None
