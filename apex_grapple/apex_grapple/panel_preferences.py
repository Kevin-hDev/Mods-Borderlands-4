"""Presentation preference stored by the SDK alongside existing mod options."""

from mods_base import SpinnerOption
from .panel_theme import PAGES

LANGUAGES = ("EN", "FR")
language = SpinnerOption("menu_language", "EN", list(LANGUAGES), is_hidden=True)
CONTROLLER_ICONS = ("PS5", "XSX")
# Kevin chose PlayStation when the game's reported family is inconclusive (2026-09-21).
controller_icons = SpinnerOption("controller_icons", "PS5", list(CONTROLLER_ICONS), is_hidden=True)
# Store a stable page name so repeated tuning and restarts return to the same tab.
last_page = SpinnerOption("menu_last_page", PAGES[0], list(PAGES), is_hidden=True)
