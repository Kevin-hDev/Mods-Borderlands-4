"""Which modules and which menu lines make up each movement, so a movement can be turned off or shipped on its own.

Kevin's rule, 2026-09-18: one mod is one movement. Two movements were sharing a module without anyone seeing it — the
ground speeds rode on the auto sprint's switch, so turning the auto sprint off quietly gave the game's own speeds
back. Nothing in the code stated the rule, so nothing caught the breach; it was found twice, both times by accident.

This file states it. test_movement_rules.py checks the code against it, and the separate file per movement
(conception, decision 2) is built from it. Every exception carries its reason here, so none can be added in silence.
"""

from dataclasses import dataclass

# Read by every movement and owned by none: the game's fields, the settings, the frame loop, the menu. jump_report
# writes diagnostic lines about any jump, whichever movement produced it.
SHARED = ("__init__", "frame", "game", "jump_report", "menu", "movements", "ownership", "report", "settings")

# Settings any movement may read: they describe how the character moves, not another movement's behaviour.
# LONGEST_SLIDE_S is read by the slides and by the landing slide's safety net, which belong to two movements.
SHARED_SETTINGS = ("speeds", "LONGEST_SLIDE_S")


@dataclass(frozen=True)
class Movement:
    name: str
    modules: tuple[str, ...]
    menu_groups: tuple[str, ...]
    # Why it cannot be switched off. Empty means it has a switch, which is what the rule expects.
    always_on_because: str = ""
    # Why one switch carries two movements. Empty means it carries exactly one, which is what the rule expects.
    one_switch_because: str = ""
    # Why it takes more than one menu line. Empty means it takes exactly one, which is what the rule expects.
    two_lines_because: str = ""


MOVEMENTS = (
    Movement("Movement", ("ground_speed",), ("movement_menu",),
             always_on_because="a walking speed has no off state; the game's own values are named in the sliders, so "
                               "a player who wants them back types them in"),
    Movement("Auto sprint", ("sprint",), ("auto_sprint_menu",)),
    Movement("Slides", ("slide", "slide_physics", "slide_direction", "slide_steering", "axle_slide"),
             ("slides_menu", "axle_slide_menu"),
             two_lines_because="the Axle slide is a slide, and the one exception Kevin named to one movement per mod "
                               "(2026-09-18): it keeps its own line because it is off by default and has five "
                               "settings of its own"),
    Movement("Dash", ("dash",), ("dash_menu",)),
    Movement("Ground slam and landing slide", ("air_crouch", "air_actions", "air_bindings", "air_keys"),
             ("air_crouch_menu",),
             one_switch_because="both need the crouch key blocked, and that block is what removes the game's own slam "
                                "on a held crouch; two switches would allow a state where the block stays on while "
                                "the player asked for neither, losing them the held-crouch slam with no way to tell "
                                "why (Kevin, 2026-09-18)"),
    Movement("Air / tap strafe", ("air_strafe",), ("air_strafe_menu",)),
    Movement("Heavier fall", ("heavier_fall", "jump_goals"), ("heavier_fall_menu",)),
    Movement("Wall climb", ("wall_climb", "wall_sense", "climb_aim", "climb_rules", "climb_refusal",
                            "climb_animation", "jump_press", "air_jumps"), ("wall_climb_menu",)),
)


def owner(module: str) -> Movement | None:
    """The movement a module belongs to, or None when it is shared."""
    for movement in MOVEMENTS:
        if module in movement.modules:
            return movement
    return None
