"""Apex Movement: brings Apex Legends style movement to Borderlands 4.

The same code builds the full pack and each separate file: pack.py says which movements this one carries, and every
registration below is skipped when it does not. The order stays as written, so a file carrying two movements runs
them in the same order the full pack does.
"""

import sys
from typing import Any

from mods_base import build_mod

from . import (
    air_crouch, air_strafe, dash, family, frame, ground_speed, heavier_fall, jump_report, menu, movements, pack,
    report, settings, slide, slide_direction, slide_physics, slide_steering, sprint, wall_climb,
)

__version__ = "1.0.0"
__author__ = "kevin-hDev"


def _register(name: str, module: Any, *switches: Any) -> None:
    if pack.carries_module(module.__name__.rsplit(".", 1)[-1]):
        frame.register(name, module, *switches)


# Which module belongs to which movement is stated in movements.py, and test_movement_rules.py checks this list
# against it: every movement takes its own switch, and no module rides on a neighbour's.
# No switch: a walking speed has no off state, and the game's own values are named in the sliders.
_register("ground_speed", ground_speed)
_register("auto_sprint", sprint, settings.auto_sprint)
# Before the slide speed: at a slide's end it puts the speed curve back first, and the slide speed reads that curve.
_register("slide_physics", slide_physics, settings.slides)
_register("slide", slide, settings.slides)
_register("momentum_slides", slide_direction, settings.slides, settings.momentum_slides)
# The Axle slide's switch: off, the normal slide keeps the game's steering. Its boosts are read by slide and slide_physics.
_register("slide_steering", slide_steering, settings.slides, settings.axle_slide)
_register("dash", dash, settings.dash)
_register("air_crouch", air_crouch, settings.air_crouch)
_register("air_strafe", air_strafe, settings.air_strafe)
_register("heavier_fall", heavier_fall, settings.heavier_fall)
# Last: it writes the velocity in the air, and no movement registered before it does.
_register("wall_climb", wall_climb, settings.wall_climb)
# After every movement: it reports the jump that just left the ground, once the others have written their speeds.
_register("jump_report", jump_report)


def _carried() -> list[str]:
    return [movement.name for movement in movements.MOVEMENTS if pack.carries(movement.name)]


def _on_enable() -> None:
    report.reset()
    # Two files running one movement would fight over the same game field, and the one stopping last would put back
    # what the other had written. Staying off is the only safe answer; the player picks which file to keep.
    clash = family.clash(__name__, _carried())
    if clash:
        report.warning(f"{clash}: this file stays off, remove one of the two")
        mod.disable()
        return
    # Tested with no other movement mod; Auto Sprint writes the same ground speed, so the last writer would win.
    if "auto_sprint" in sys.modules:
        report.warning("the Auto Sprint mod is also loaded; both set the ground speed, disable one of them")
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    for failure in frame.stop_all():
        report.error_once(failure, failure)
    report.note("disabled, game values restored")


mod = build_mod(
    name=pack.NAME,
    options=menu.MENU,
    hooks=[frame.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
