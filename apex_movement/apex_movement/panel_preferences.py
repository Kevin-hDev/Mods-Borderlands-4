"""Menu preferences as hidden SDK options, with stable page IDs from menu.ALL."""

from mods_base import BoolOption, SliderOption, SpinnerOption

from . import menu, pack
from .panel_scroll import last_scroll
from .panel_theme import SIZES, THEMES

LANGUAGES = ("EN", "FR")
_COMMANDS = ("commands",) if pack.is_full() else ()
# Last, so a page index saved before the Options tabs (2026-10-06) still names the same page.
_LANGUAGE = ("language",) if pack.is_full() else ()
# After it for the same reason: the DYNAMIC CAMERA tab came later the same day.
_DYNAMIC = ("dynamic_camera",) if pack.is_full() else ()
# And the SHOULDER VIEW tab after it (2026-10-07), then AIMING and SENSITIVITY (2026-10-08).
_SHOULDER = ("shoulder", "aiming", "sensitivity") if pack.is_full() else ()
# And OMNI DIRECTION after them (2026-10-09).
_OMNI = ("omni_direction",) if pack.is_full() else ()
PAGE_KEYS = (*tuple(group.identifier.removesuffix("_menu") for group in menu.ALL), *_COMMANDS, "options",
             *_LANGUAGE, *_DYNAMIC, *_SHOULDER, *_OMNI)
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
ALL = (french, controller_icons, last_page, theme, window_size, last_scroll)
