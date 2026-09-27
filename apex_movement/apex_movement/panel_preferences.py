"""Menu preferences as hidden SDK options, with stable page IDs from menu.ALL."""

from mods_base import BoolOption, SliderOption, SpinnerOption

from . import menu, pack

LANGUAGES = ("EN", "FR")
_COMMANDS = ("commands",) if pack.is_full() else ()
PAGE_KEYS = (*tuple(group.identifier.removesuffix("_menu") for group in menu.ALL), *_COMMANDS, "options")
french = BoolOption("menu_french", False, is_hidden=True)
CONTROLLER_ICONS = ("PS5", "XSX")
controller_icons = SpinnerOption("controller_icons", "PS5", list(CONTROLLER_ICONS), is_hidden=True)
# mods_base refuses a slider whose step is wider than its range, which a one-page menu would have. Model.page
# already ignores a saved index past the pages.
last_page = SliderOption("menu_last_page", 0, 0, max(1, len(PAGE_KEYS) - 1),
                         step=1, is_integer=True, is_hidden=True)
ALL = (french, controller_icons, last_page)
