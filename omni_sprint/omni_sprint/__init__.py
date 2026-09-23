"""Omni Sprint: sprint in every direction in Borderlands 4, at the game's own sprint speed.

Installs beside Apex Movement and Vehicle Driving: its own package name, hook identifier and settings file, no key
bound, and game values neither of them writes: the sprint angle limit, the body's backward run and, when its
option is on, the FOV.
"""

from mods_base import build_mod

from . import animation, fov, frame, report, settings

__version__ = "1.0.1"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    frame.reset()
    # Keep a pending FOV restoration if the previous disable could not write it back.
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    try:
        animation.stop()
    except Exception:
        report.error_once('animation_restore', 'backward animation restoration failed')
    try:
        fov.stop()
    except Exception as exc:
        report.error_once("fov_restore", f"FOV give back failed: {exc!r}")
    restored, left = frame.stop()
    line = f"disabled, game sprint limit put back in {restored} movement definition(s)"
    if left:
        line += f", {left} left alone: no longer recognised in memory"
    report.note(line)


mod = build_mod(
    name="Omni Sprint",
    hooks=[frame.tick],
    options=settings.OPTIONS,
    on_enable=_on_enable,
    on_disable=_on_disable,
)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
