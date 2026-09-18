"""Apex Movement: brings Apex Legends style movement to Borderlands 4."""

import sys

from mods_base import build_mod

from . import (
    air_crouch, air_strafe, dash, frame, ground_speed, heavier_fall, jump_report, menu, report, settings, slide,
    slide_direction, slide_physics, slide_steering, sprint, wall_climb,
)

__version__ = "1.0.0"
__author__ = "kevin-hDev"

# No switch: the raised walk and sprint speeds apply whether the auto sprint is on or off (Nexus page, 2026-09-18).
frame.register("ground_speed", None, ground_speed)
frame.register("auto_sprint", settings.auto_sprint, sprint)
# Before the slide speed: at a slide's end it puts the speed curve back first, and the slide speed reads that curve.
frame.register("slide_physics", None, slide_physics)
frame.register("slide", None, slide)
frame.register("momentum_slides", settings.momentum_slides, slide_direction)
# The Axle slide's switch: off, the normal slide keeps the game's steering. Its boosts are read by slide and slide_physics.
frame.register("slide_steering", settings.axle_slide, slide_steering)
frame.register("dash", None, dash)
frame.register("air_crouch", settings.air_crouch, air_crouch)
frame.register("air_strafe", settings.air_strafe, air_strafe)
frame.register("heavier_fall", settings.heavier_fall, heavier_fall)
# Last: it writes the velocity in the air, and no movement registered before it does.
frame.register("wall_climb", settings.wall_climb, wall_climb)
# After every movement: it reports the jump that just left the ground, once the others have written their speeds.
frame.register("jump_report", None, jump_report)


def _on_enable() -> None:
    report.reset()
    # Tested with no other movement mod; Auto Sprint writes the same ground speed, so the last writer would win.
    if "auto_sprint" in sys.modules:
        report.warning("the Auto Sprint mod is also loaded; both set the ground speed, disable one of them")
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    for failure in frame.stop_all():
        report.error_once(failure, failure)
    report.note("disabled, game values restored")


mod = build_mod(
    name="Apex Movement",
    options=menu.MENU,
    hooks=[frame.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
