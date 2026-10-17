"""Co-op Duel: the host and his guest fight each other in a co-op game, anywhere in the world. The one who falls stays
KO 3 seconds, then stands up where he fell, and the next round starts; the score shows at each round. Only the host
needs the mod (docs/duel). Its window opens from the SDK's list of mods or by its key, F9 at first; another key, N at
first, starts or stops the duel (keys.py)."""

from mods_base import build_mod
from .settings_persistence import AtomicMod

from . import duel, heartbeat, keys, panel_open, panel_preferences, report
from .pack import NAME

__version__ = "1.0.0"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    report.note("enabled", version=__version__)


def _on_disable() -> None:
    # Switched off mid-duel, every player is given back to normal: the hook that would end it is gone with the mod.
    try:
        duel.stop("mod_off", show=False)
        duel.hide()
    except Exception as error:
        report.error_once("disable", f"the duel could not be ended cleanly ({type(error).__name__})")
    report.note("disabled")


mod = build_mod(
    cls=AtomicMod,
    name=NAME,
    # The window's own preferences (language, last page) and the two keys, hidden in the SDK's menu.
    options=[*panel_preferences.ALL, *(shortcut.option for shortcut in keys.ALL)],
    keybinds=[shortcut.bind for shortcut in keys.ALL],
    hooks=[heartbeat.tick],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
# build_mod has read the settings file (mods_base, register_mod): each keybind takes its saved key.
keys.align()
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
