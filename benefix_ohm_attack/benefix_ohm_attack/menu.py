"""The window's pages: BEAM, with its two cards, then COMMANDS, a card per command (control_config.py). Kevin chose
the page on 2026-10-01 from sketch M1 (docs/attaque-rayon/esquisses_menu/M1.png): everything on one page, the element
between two arrows. The window itself is Apex Heirloom's, generated (docs/attaque-rayon/outils/menu_window.py); it
reads every name below.
"""

from mods_base import NestedOption

from . import settings

# Left out of the mod's options: saved values stay at the top level of the settings file, as before the window.
beam_page = NestedOption(
    "beam_menu", list(settings.ALL),
    display_name="Beam",
    description="Hold the beam's key: your left hand rises and fires a beam at what you aim at.",
)
MENU = [beam_page]
# Each page's cards, top to bottom: (the card's name, its rows). The first card wears the page's own name and
# sentence; another one's words are <name> and <name>_desc in panel_en.py and panel_fr.py.
CARDS = {
    "beam": (("beam", (settings.element, settings.damage)),
             ("energy", (settings.show_bar, settings.drain, settings.regen, settings.regen_delay))),
}
# The pages a player can open, in the window's order (panel_theme.PAGES).
SHOWN_PAGES = ("beam", "controls")
# Rows whose choices show as two arrows around the chosen name, its place among them in the value box (sketch M1).
ARROWS = frozenset((settings.element.identifier,))
# What the heirloom's window can also do and this one has no use for: a row or a command's card greyed with a
# switch, a sentence at the top of a page, a row hidden or greyed by the window's values, a picture beside the title.
DEPENDS_ON: dict = {}
COMMANDS_DEPEND_ON: dict = {}
NOTICES: dict = {}
ACTIVE_WHEN: dict = {}
SHOWN_WHEN: dict = {}
PICTURES: dict = {}
