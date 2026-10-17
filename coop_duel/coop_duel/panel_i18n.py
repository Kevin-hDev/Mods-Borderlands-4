# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under Co-op Duel's
# names. Its comments may speak of other mods. Never edited by hand: docs/duel/outils/menu_window.py
# writes this file.
"""One language lookup for the settings window, with English fallback."""

from importlib import import_module

from . import panel_en
from .panel_preferences import LANGUAGES

# Each language past English keeps its TEXT, OPTIONS and GROUPS in panel_<code>.py; LANGUAGES says which ones ship.
TABLES = {code: import_module(f".panel_{code.lower()}", __package__) for code in LANGUAGES if code != "EN"}


def text(key, language):
    table = TABLES.get(language)
    return table.TEXT[key] if table is not None and key in table.TEXT else panel_en.TEXT[key]


def option_text(option, language):
    table = TABLES.get(language)
    if table is not None and option.identifier in table.OPTIONS:
        return table.OPTIONS[option.identifier]
    return option.display_name, option.description


def group_text(group, key, language):
    table = TABLES.get(language)
    return table.GROUPS[key] if table is not None and key in table.GROUPS else group.description


def number(option, value):
    digits = 0 if option.is_integer else max(0, len(str(option.step).rstrip("0").split(".")[-1]))
    return f"{value:.{digits}f}"
