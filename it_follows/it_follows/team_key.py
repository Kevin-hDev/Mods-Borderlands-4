"""The key that launches the companions' team in game, or stops it (spec-compagnons.md: « Dans les options d'It
Follows, une ligne pour une touche personnalisable qui lance ou arrête l'équipe »), F8 unless the player chose another
on the OPTIONS page: F5 opens It Follows' window (open_key.py), F6 BL4 Arena's and F7 Third Person & FOV's (Kevin,
22 October 2026: F8 and F9 are the two left for our mods). Its one authority is a hidden option of the settings file,
as the window's key's; the SDK's keybind is given its key from it (align). The two keys are never the same one
(panel_options.py). The option is named companions_key: trial 191 wrote F7 under team_key, never published, and a new
name leaves that F7 behind instead of keeping it.

Pressed: the team the COMPANIONS page keeps, with each one's choice, as LAUNCH THE TEAM starts it; while the team is
on, it stops. A team still empty starts nothing. Each press is written in the log with what it did."""

from mods_base import HiddenOption, keybind

from . import open_key, report, session
from . import companion_choices as choices

DEFAULT = "F8"
# The team's key when the settings file gives the window F8 by hand (OPTIONS refuses it): F9, the other key Kevin left
# to our mods (decision 52 of docs/renforts), also Co-op Duel's; only a file edited so can reach it.
SPARE = "F9"

option = HiddenOption("companions_key", DEFAULT)


def _pressed() -> None:
    from . import control_window
    if control_window.active():
        # The window is open (and the game paused): the team starts and stops from its page there.
        report.note("team_key_pressed", key=bind.key, outcome="window_open")
        return
    if session.team_on():
        outcome = session.stop_team()
    else:
        names = choices.names()
        outcome = session.start_team(names, choices.team_choices()) if names else "empty"
    report.note("team_key_pressed", key=bind.key, outcome=outcome)


bind = keybind("toggle_team", DEFAULT, _pressed, display_name="Launch or stop the team",
               description="The key that launches your companions, or stops them, in game.", is_hidden=True)


def key() -> str:
    """The chosen key's Unreal name, the default for a value the file holds that is no key or is the window's key
    (one press would open the window and launch the team at once); SPARE when the window's key is the default."""
    value, window = option.value, open_key.key()
    if open_key.valid(value) and value != window:
        return value
    return DEFAULT if DEFAULT != window else SPARE


def align() -> bool:
    """The SDK's keybind given the option's key, when they differ; whether it was."""
    if bind.key == key():
        return False
    bind.key = key()
    report.note("team_key_bound", key=bind.key)
    return True
