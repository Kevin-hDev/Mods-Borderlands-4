"""Tests the menu: one line per movement, each holding its switch and settings, its label following the switch."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import menu, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the menu holds one line per movement, named as the game names it", [group.display_name for group in menu.MENU]
      == ["Movement", "Auto sprint (On)", "Slides", "Axle slide (Off)", "Dash", "Slam and landing slide (On)",
          "Air / tap strafe (On)", "Heavier fall (On)", "Wall climb (On)"])
check("the speeds have their own line, apart from the auto sprint switch",
      menu.movement.children == [settings.walk_speed, settings.sprint_speed]
      and menu.auto_sprint.children == [settings.auto_sprint])
check("each movement's line opens its switch and settings",
      menu.heavier_fall.children == [settings.heavier_fall, settings.fall_weight, settings.jump_height_bonus])
check("slides hold the direction switch, speed, distance, downhill pull and top speed, and no steering",
      menu.slides.children == [settings.momentum_slides, settings.slide_speed, settings.slide_distance,
                               settings.slide_downhill_pull, settings.slide_max_speed])
check("the Axle slide holds its switch, steering and three boosts", menu.axle_slide.children == [
    settings.axle_slide, settings.axle_steering, settings.axle_speed_boost, settings.axle_flat_distance_boost,
    settings.axle_slope_boost,
])
check("the dash holds its distance", menu.dash.children == [settings.dash_distance])
check("the slam line holds its landing minimum, since the same switch carries both",
      settings.landing_slide_min_speed in menu.air_crouch.children)
check("air strafe holds its acceleration", settings.air_acceleration in menu.air_strafe.children)
check("the wall climb holds its switch, height, speed, diagonal and wait", menu.wall_climb.children == [
    settings.wall_climb, settings.climb_height, settings.climb_speed, settings.climb_lean, settings.reclimb_delay,
])

every_option = [option for group in menu.MENU for option in group.children]
check("every setting appears exactly once", len(every_option) == len(set(map(id, every_option))) == 26)
check("group identifiers differ from the old top-level ones, so old settings files load cleanly",
      {group.identifier for group in menu.MENU}.isdisjoint({option.identifier for option in every_option}))

settings.air_strafe.value = False
check("switching a movement off shows on its line", menu.air_strafe.display_name == "Air / tap strafe (Off)")
settings.air_strafe.value = True
check("switching it back on shows too", menu.air_strafe.display_name == "Air / tap strafe (On)")
check("other lines are left alone", menu.heavier_fall.display_name == "Heavier fall (On)")
settings.axle_slide.value = True
check("switching the Axle slide on shows on its line", menu.axle_slide.display_name == "Axle slide (On)")
settings.axle_slide.value = False

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
