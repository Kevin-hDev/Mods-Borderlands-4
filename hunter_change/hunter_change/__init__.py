"""Hunter Change: become another hunter in a game, keeping its level, backpack and story, each hunter with their own
skill tree; or only wear another hunter's look."""

from mods_base import build_mod
from .settings_persistence import AtomicMod

from . import leave, lifecycle, panel_open, panel_preferences, report, wardrobe
from .pack import NAME

__version__ = "1.0.2"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    lifecycle.reset()
    report.note(f"enabled, version {__version__}")


def _on_disable() -> None:
    try:
        wardrobe.undress()
    except Exception as error:
        report.error_once("undress", f"the own look could not be given back: {error!r}")
    try:
        leave.cancel()
    except Exception as error:
        report.error_once("leave", f"the hunter change asked in the game could not be dropped: {error!r}")
    lifecycle.reset()
    report.note("disabled")


mod = build_mod(
    cls=AtomicMod,
    name=NAME,
    # The window's own preferences (language, last page), hidden in the SDK's menu.
    options=[*panel_preferences.ALL],
    hooks=[lifecycle.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
panel_open.install(mod)

if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
