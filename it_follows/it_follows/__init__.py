"""It Follows: two modes, never at once (decision 80). The Horde: every enemy around the hunter comes for him, without
end, during a run. The normal mode: the game played as usual, its enemies reworked.

Kevin, 2026-10-10: « un clic et tous les ennemis, peu importe où ils sont, se mettent tous à se déplacer en se dirigeant
vers le chasseur » ; named after the film he gave as its reference (decision 46, docs/RUN). Each mode is started and
stopped in the mod's window (menu.py), opened from the SDK's list of mods or by its key, F5 at first (open_key.py). The
normal mode on stays on from one game launch to the next: the mod turns it on again when it is enabled.
"""

from mods_base import build_mod

from . import colours, kept, lost_loot, open_key, options, panel_open, panel_preferences, report, resolution
from . import session, start_point, updates, welcome
from .normal import hardcore, options as normal_options
from .settings_persistence import AtomicMod

__version__ = "1.0.8"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.note("enabled", version=__version__)
    lost_loot.start()
    resolution.start()
    colours.start()
    if normal_options.on.value is True:
        outcome = session.start_normal(normal_options.read())
        report.note("normal_resumed", outcome=outcome)
        if outcome == "start_failed":
            # Saved by mods_base right after on_enable (Mod.enable), even at launch, before this package's mod
            # exists: a mode that failed is not tried again at the next launch (decision 93).
            normal_options.on.value = False


def _on_disable() -> None:
    start_point.cancel("mod_disabled")
    session.stop("mod_disabled")
    # The choice to be on stays in the settings file: the mode comes back when the mod is enabled again.
    session.stop_normal("mod_disabled")
    lost_loot.stop()
    resolution.stop()
    colours.stop()
    report.note("disabled")


mod = build_mod(
    cls=AtomicMod,
    name="It Follows",
    # The run's settings and the normal mode's, then the window's own (language, theme, window size, last page), the
    # welcome edition last seen, the version whose update notes were seen last, the last runs, the Hardcore's kills and
    # the key that opens the window, hidden in the SDK's menu.
    options=[*options.ALL, *normal_options.ALL, *panel_preferences.ALL, welcome.seen, updates.seen, kept.option,
             hardcore.option, open_key.option],
    keybinds=[open_key.bind],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
# build_mod has read the settings file (mods_base, register_mod).
options.shelve()
# Set here, not in options.py: lost_loot, resolution and colours import options.
options.lost_loot.on_change_while_enabled = lost_loot.changed
options.resolution.on_change_while_enabled = resolution.changed
options.colours.on_change_while_enabled = colours.switched
options.colour_profile.on_change_while_enabled = colours.chosen
kept.load()
hardcore.load()
open_key.align()
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
