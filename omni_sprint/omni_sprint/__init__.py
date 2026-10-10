"""Omni Sprint: sprint in every direction in Borderlands 4, at the game's own sprint speed.

Installs beside Apex Movement and Vehicle Driving: its own package name, hook identifier, settings file and window.
The sprint angle limit and the body's backward run are written by the camera runtime the camera mods share
(docs/omni_direction/spec-omni-direction.md), from this mod's switch. Its camera settings apply while Apex
Movement's are not in use.
"""

from mods_base import build_mod
from .settings_persistence import AtomicMod

from . import camera, frame, panel_open, panel_preferences, report, settings

__version__ = "1.2.0"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    frame.reset()
    settings.commands.align()
    camera.start()
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    # The shared runtime puts the sprint limit and the backward run back once no mod asks for them any more.
    try:
        camera.stop()
    except Exception as exc:
        report.error_once("camera_restore", f"camera give back failed: {exc!r}")
    try:
        frame.stop()
    except Exception as exc:
        report.error_once("sprint_restore", f"the open sprint's own copy could not give everything back: {exc!r}")
    report.note("disabled")


mod = build_mod(
    cls=AtomicMod,
    name="Omni Sprint",
    hooks=[frame.tick],
    keybinds=settings.commands.binds,
    # The window's language and page are hidden options: the SDK menu still lists only settings.OPTIONS.
    options=[*settings.OPTIONS, *panel_preferences.ALL],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
