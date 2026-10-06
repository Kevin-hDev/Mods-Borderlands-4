"""Vehicle Driving: livelier vehicles in Borderlands 4, with top speed, acceleration, turning, jump height, grip,
reverse, boost, toughness, weapon damage and camera views.

Installs beside Apex Movement: its own package name, hook identifier and settings file, one key of its own (the camera
view's, never blocked), and no game value in common (spec section 4, Kevin's requirement of 2026-09-18).
"""

from mods_base import build_mod
from .settings_persistence import AtomicMod

from . import command_keys, frame, panel_open, panel_preferences, report, settings, view_key
from .vehicle_unlock_runtime import runtime as vehicle_runtime

__version__ = "1.0.7"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    for line in settings.keep_in_bounds():
        report.warning(line)
    # mods_base enables the mod after loading its settings: the view key's bind takes its option's key.
    command_keys.KEYS.align()
    report.note(f"enabled, version {__version__}")
    vehicle_runtime.protection_runtime.start('vehicle_driving')


def _on_disable() -> None:
    if not vehicle_runtime.protection_runtime.stop('vehicle_driving'):
        mod.enable()
        report.note('disable refused: vehicle protection restoration failed; restart required')
        return
    for failure in frame.stop_all():
        report.error_once(failure, failure)
    report.note("disabled, game values restored")


mod = build_mod(
    cls=AtomicMod,
    name="Vehicle Driving",
    # Every setting stays a top-level key: the six of 1.0 load unchanged, and a 1.0 file leaves the new ones at their
    # defaults (mods_base's load_options_dict skips a key the file lacks).
    options=[*settings.OPTIONS, *settings.CAMERA_OPTIONS, *view_key.OPTIONS, *panel_preferences.ALL],
    keybinds=view_key.BINDS,
    hooks=[frame.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
