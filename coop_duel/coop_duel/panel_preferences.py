# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under Co-op Duel's
# names. Its comments may speak of other mods. Never edited by hand: docs/duel/outils/menu_window.py
# writes this file.
"""Menu preferences as hidden SDK options, with stable page IDs from menu.ALL."""

from mods_base import BoolOption, SliderOption, SpinnerOption

from . import menu
from .panel_scroll import last_scroll
from .panel_theme import SIZES, THEMES

# Chinese only in a window whose every text exists in it, as outils/menu_languages.py decides.
LANGUAGES = ("EN", "FR", "ZH")
_COMMANDS = ()
PAGE_KEYS = tuple(group.identifier.removesuffix("_menu") for group in menu.ALL)
# The language as a code, since a third one came (Chinese, 2026-10-12). A value this mod does not offer reads as
# English (panel_model.py).
language = SpinnerOption("menu_language", "EN", list(LANGUAGES), is_hidden=True)
# The yes/no French was saved as before: still read, so a player who chose French keeps it, and set back to no
# the first time they pick a language.
french = BoolOption("menu_french", False, is_hidden=True)
CONTROLLER_ICONS = ("PS5", "XSX")
controller_icons = SpinnerOption("controller_icons", "PS5", list(CONTROLLER_ICONS), is_hidden=True)
# mods_base refuses a slider whose step is wider than its range, which a one-page menu would have. Model.page
# already ignores a saved index past the pages.
last_page = SliderOption("menu_last_page", 0, 0, max(1, len(PAGE_KEYS) - 1),
                         step=1, is_integer=True, is_hidden=True)
# Each mod keeps its own theme, as it keeps its language (Kevin, 2026-10-06).
theme = SpinnerOption("menu_theme", THEMES[0], list(THEMES), is_hidden=True)
# Each mod keeps its own window size, as its theme (Kevin, 2026-10-06).
window_size = SpinnerOption("menu_window_size", SIZES[0], list(SIZES), is_hidden=True)
ALL = (language, french, controller_icons, last_page, theme, window_size, last_scroll)
