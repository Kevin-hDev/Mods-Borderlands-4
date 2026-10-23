"""Companions: a team of up to eight companions, Vault Hunters and allies of the game, who follow the hunter and fight
beside him, without It Follows (spec-compagnons.md, « Le mod dédié »). The team is chosen and launched in the mod's
window (menu.py), opened from the SDK's list of mods, or by a key the player chooses, none at first (decision 71 of
docs/renforts); the team's key, F8 at first, launches it or stops it in game.

The companions' code is the characters' package, the same one It Follows carries (decision 69): when both mods are
on, It Follows leads the team, and Companions' does not start (characters/companions/owners.py).
"""

from mods_base import build_mod

from . import open_key, panel_open, panel_preferences, report, session, settings, team_key
from .characters.companions import owners, team as companions_team
from .settings_persistence import AtomicMod

__version__ = "1.0.0"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.note("enabled", version=__version__)
    # Companions leads the team only while no mod marked first (It Follows) is on.
    owners.switched_on(companions_team.OWNER)


def _on_disable() -> None:
    # Each stop on its own: one that raises must not leave the next undone with the mod disabled.
    failed = []
    for name, stop in (("team", lambda: session.stop_team("mod_disabled")),
                       ("team_owner", lambda: owners.switched_off(companions_team.OWNER))):
        try:
            stop()
        except Exception as error:
            failed.append(f"{name}:{type(error).__name__}")
    report.note("disabled", **({"failed": failed} if failed else {}))


mod = build_mod(
    cls=AtomicMod,
    name="Companions",
    # The team's five settings and the bars, the team and the outfits, then the window's own (language, theme,
    # window size, last page), the key that opens the window and the team's, hidden in the SDK's menu.
    options=[*settings.TEAM, settings.bars, *settings.HIDDEN, *panel_preferences.ALL, open_key.option,
             team_key.option],
    keybinds=[open_key.bind, team_key.bind],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
# build_mod has read the settings file: the SDK's keybinds take the keys the player chose.
open_key.align()
team_key.align()
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
