"""Vehicle Driving: livelier vehicles in Borderlands 4, with top speed, acceleration, turning, jump height and grip.

Installs beside Apex Movement: its own package name, hook identifier and settings file, no key bound, and no game
value in common (spec section 4, Kevin's requirement of 2026-09-18).
"""

from mods_base import build_mod

from . import frame, panel_open, panel_preferences, report, settings

__version__ = "1.0.1"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    for line in settings.keep_in_bounds():
        report.warning(line)
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    for failure in frame.stop_all():
        report.error_once(failure, failure)
    report.note("disabled, game values restored")


mod = build_mod(
    name="Vehicle Driving",
    # Keep the six original top-level keys so existing players' saved values load unchanged.
    options=[*settings.OPTIONS, *panel_preferences.ALL],
    hooks=[frame.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
