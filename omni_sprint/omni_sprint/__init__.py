"""Omni Sprint: sprint in every direction in Borderlands 4, at the game's own sprint speed.

Installs beside Apex Movement and Vehicle Driving: its own package name, hook identifier and settings file, no key
bound, and game values neither of them writes: the sprint angle limit, the body's backward run and, when its
option is on, the FOV.
"""

from mods_base import build_mod

from . import animation, camera, frame, report, settings

__version__ = "1.0.2"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    frame.reset()
    camera.start()
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    try:
        animation.stop()
    except Exception:
        report.error_once('animation_restore', 'backward animation restoration failed')
    try:
        camera.stop()
    except Exception as exc:
        report.error_once("camera_restore", f"camera give back failed: {exc!r}")
    restored, left = frame.stop()
    line = f"disabled, game sprint limit put back in {restored} movement definition(s)"
    if left:
        line += f", {left} left alone: no longer recognised in memory"
    report.note(line)


mod = build_mod(
    name="Omni Sprint",
    hooks=[frame.tick],
    keybinds=[settings.third_person_bind],
    options=settings.OPTIONS,
    on_enable=_on_enable,
    on_disable=_on_disable,
)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
