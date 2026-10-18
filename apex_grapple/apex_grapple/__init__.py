"""Apex Grapple: the grapple of Apex Legends in Borderlands 4, a rope that pulls instead of a throw.

The game's own grapple is a throw: the whole arc is worked out the moment you press, and you have no
say in it afterwards. This mod replaces it with a constant force toward whatever you aimed at, while
the move stick keeps steering you — which is what lets you shoot at one point and end up somewhere
else.

It writes the player's velocity and nothing else, so it changes no value another mod owns. Apex
Movement's gravity, air control and jump counters are read, never written.

The model is measured, not guessed: docs/apex_grapple/spec-apex-grapple.md says what it does,
docs/candidats/grappin.md holds the numbers and where each came from.
"""

from mods_base import build_mod
from .settings_persistence import AtomicMod

from . import control_console_menu, control_menu, coop_link, coop_messages, frame, menu, report, settings, settings_moved
from . import updates

# Research observers are archived: their synchronous scans caused first-shot stalls.
__version__ = "1.0.12"
__author__ = "kevin-hDev"


def _on_enable() -> None:
    report.reset()
    for line in settings.keep_in_bounds():
        report.warning(line)
    report.note(f"enabled, version {__version__}")
    # The values in use, not the defaults in the code: the player's settings file wins over them.
    report.note(f"settings in use: {settings.summary()}")


def _on_disable() -> None:
    frame.stop()
    report.note("disabled")


mod = build_mod(
    cls=AtomicMod,
    name="Apex Grapple",
    options=[*menu.MENU, updates.seen],
    hooks=[frame.tick, coop_link.on_send, coop_messages.on_message],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
# build_mod has loaded the settings file by now (mods_base, mod_list.register_mod, read on 2026-10-14).
settings_moved.adopt(mod, menu.MOVED)
control_console_menu.install(mod, control_menu.MENU)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
    updates.new_player(mod, __version__)
