"""The menu: one line per movement, which opens that movement's switch and settings.

In 0.4.0 every switch and every slider had its own line, so one movement could take three lines; Kevin found it hard
to follow (2026-09-17: "pourquoi pas faire plus simple ? y'en a qui risquent pas de comprendre"). A movement's line
shows its switch state, kept current on every change, the settings file included: mods_base runs on_change_anytime
when it loads a value. Only options whose movement works are shown (0.1.0 lesson: idle switches read as broken).

The group identifiers differ from the 0.4.0 top-level ones: an older settings file then loads without errors, its old
keys are ignored and the defaults apply.
"""

from typing import Any

from mods_base import NestedOption

from . import settings


def _label(title: str, on: bool) -> str:
    return f"{title} ({'On' if on else 'Off'})"


def _group(identifier: str, title: str, description: str, switch: Any, *sliders: Any) -> Any:
    group = NestedOption(identifier, [switch, *sliders], display_name=_label(title, bool(switch.value)),
                         description=description)

    def follow(_option: Any, value: bool) -> None:
        group.display_name = _label(title, bool(value))

    switch.on_change_anytime = follow
    return group


# The names follow the game's own option screen (Sprint, Slide, Dash, Slam), so that a line of the menu and a line of
# the Nexus page name the same move. "Air crouch" named nothing a Borderlands player would recognise (Kevin,
# 2026-09-18).
movement = NestedOption(
    "movement_menu", [settings.walk_speed, settings.sprint_speed],
    display_name="Movement", description="How fast you walk and sprint. These apply whether auto sprint is on or off.",
)
auto_sprint = _group(
    "auto_sprint_menu", "Auto sprint", "Sprint on a fully pushed stick, without pressing anything.",
    settings.auto_sprint,
)
slides = NestedOption(
    "slides_menu", [settings.momentum_slides, settings.slide_speed, settings.slide_distance, settings.slide_downhill_pull,
                    settings.slide_max_speed],
    display_name="Slides", description="How slides start, go on, and slow down.",
)
axle_slide = _group(
    "axle_slide_menu", "Axle slide", "Steer your slides with the move stick, and boost every slide, as Axle does.",
    settings.axle_slide, settings.axle_steering, settings.axle_speed_boost, settings.axle_flat_distance_boost,
    settings.axle_slope_boost,
)
dash = NestedOption(
    "dash_menu", [settings.dash_distance],
    display_name="Dash", description="How far a dash goes, at the game's own speed.",
)
air_crouch = _group(
    "air_crouch_menu", "Slam and landing slide",
    "Jump and crouch together to slam, and crouch held in the air to slide the moment you land.",
    settings.air_crouch, settings.landing_slide_min_speed,
)
air_strafe = _group(
    "air_strafe_menu", "Air / tap strafe", "Change direction in the air almost at once.",
    settings.air_strafe, settings.air_acceleration,
)
heavier_fall = _group(
    "heavier_fall_menu", "Heavier fall", "A stronger gravity that keeps every jump at its height, plus extra height.",
    settings.heavier_fall, settings.fall_weight, settings.jump_height_bonus,
)
wall_climb = _group(
    "wall_climb_menu", "Wall climb", "Climb up walls and pull yourself over the top, as in Apex Legends.",
    settings.wall_climb, settings.climb_height, settings.climb_speed, settings.climb_lean, settings.reclimb_delay,
)

MENU = [movement, auto_sprint, slides, axle_slide, dash, air_crouch, air_strafe, heavier_fall, wall_climb]
