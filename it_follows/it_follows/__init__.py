"""It Follows: two modes, never at once (decision 80). The Horde: every enemy around the hunter comes for him, without
end, during a run. The normal mode: the game played as usual, its enemies reworked.

Kevin, 2026-10-10: « un clic et tous les ennemis, peu importe où ils sont, se mettent tous à se déplacer en se dirigeant
vers le chasseur » ; named after the film he gave as its reference (decision 46, docs/RUN). Each mode is started and
stopped in the mod's window (menu.py), opened from the SDK's list of mods or by its key, F5 at first (open_key.py). The
normal mode on stays on from one game launch to the next: the mod turns it on again when it is enabled.
"""

from mods_base import build_mod

from . import colours, companion_choices, kept, lost_loot, open_key, options, panel_open, panel_preferences, report
from . import resolution, session, start_point, team_key, updates, welcome
from .characters.companions import owners, team as companions_team
from .normal import hardcore, options as normal_options
from .settings_persistence import AtomicMod

__version__ = "1.0.13"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.note("enabled", version=__version__)
    # It Follows leads the companions' team before Companions when both are on (spec-compagnons.md: « It Follows
    # reste prioritaire »); switched off, it leaves the team to the other.
    owners.switched_on(companions_team.OWNER, first=True)
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
    # Each stop on its own: one that raises must not leave the next running with the mod disabled.
    failed = []
    for name, stop in (("start_point", lambda: start_point.cancel("mod_disabled")),
                       ("run", lambda: session.stop("mod_disabled")),
                       # The choice to be on stays in the settings file: the mode comes back when the mod is enabled.
                       ("normal", lambda: session.stop_normal("mod_disabled")),
                       ("team", lambda: session.stop_team("mod_disabled")),
                       ("team_owner", lambda: owners.switched_off(companions_team.OWNER)),
                       ("lost_loot", lost_loot.stop), ("resolution", resolution.stop), ("colours", colours.stop)):
        try:
            stop()
        except Exception as error:
            failed.append(f"{name}:{type(error).__name__}")
    report.note("disabled", **({"failed": failed} if failed else {}))


mod = build_mod(
    cls=AtomicMod,
    name="It Follows",
    # The run's settings and the normal mode's, the companions' team and bars, then the window's own (language, theme,
    # window size, last page), the welcome edition last seen, the version whose update notes were seen last, the last
    # runs, the Hardcore's kills, the key that opens the window and the team's, hidden in the SDK's menu.
    options=[*options.ALL, *normal_options.ALL, *companion_choices.ALL, companion_choices.bars,
             *panel_preferences.ALL, welcome.seen, updates.seen, kept.option, hardcore.option, open_key.option,
             team_key.option],
    keybinds=[open_key.bind, team_key.bind],
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
