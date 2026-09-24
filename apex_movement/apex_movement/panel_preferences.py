"""Menu preferences as hidden SDK options, with stable page IDs from menu.ALL."""

from mods_base import BoolOption, SliderOption

from . import menu

LANGUAGES = ("EN", "FR")
PAGE_KEYS = (*tuple(group.identifier.removesuffix("_menu") for group in menu.ALL), "options")
french = BoolOption("menu_french", False, is_hidden=True)
last_page = SliderOption("menu_last_page", 0, 0, len(PAGE_KEYS) - 1,
                         step=1, is_integer=True, is_hidden=True)
ALL = (french, last_page)
