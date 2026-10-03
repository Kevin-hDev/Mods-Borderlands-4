"""The window's pages: BEAM, with its two cards, LOCK, with its two, then COMMANDS, a card per command
(control_config.py). Kevin chose the BEAM page on 2026-10-01 from sketch M1 (docs/attaque-rayon/esquisses_menu/M1.png):
the element between two arrows. The LOCK page came on 2026-10-02 with the lock and the bounce he asked for, each
with its switch. The window itself is Apex Heirloom's, generated (docs/attaque-rayon/outils/menu_window.py); it
reads every name below.
"""

from mods_base import NestedOption

from . import settings

# Left out of the mod's options: saved values stay at the top level of the settings file, as before the window.
beam_page = NestedOption(
    "beam_menu", list(settings.BEAM_PAGE),
    display_name="Beam",
    description="Hold the beam's key: your left hand rises and fires a beam at what you aim at.",
)
lock_page = NestedOption(
    "lock_menu", list(settings.LOCK_PAGE),
    display_name="Lock",
    description="The beam locks onto the enemy it touches, as the Benefix Ohm I Got's does.",
)
MENU = [beam_page, lock_page]
# Each page's cards, top to bottom: (the card's name, its rows). The first card wears the page's own name and
# sentence; another one's words are <name> and <name>_desc in panel_en.py and panel_fr.py.
CARDS = {
    "beam": (("beam", (settings.element, settings.damage, settings.width)),
             ("energy", (settings.show_bar, settings.drain, settings.regen, settings.regen_delay))),
    "lock": (("lock", (settings.lock, settings.lock_delay, settings.lock_angle)),
             ("bounce", (settings.bounce,))),
}
# The pages a player can open, in the window's order (panel_theme.PAGES).
SHOWN_PAGES = ("beam", "lock", "controls")
# Rows whose choices show as two arrows around the chosen name, its place among them in the value box (sketch M1).
ARROWS = frozenset((settings.element.identifier,))
# A row that changes nothing while its switch is off greys and stays still, as in our other windows
# (docs/mokup/menu_mods/decisions.md, 2026-09-26): each tuple needs one of its switches on. The catch and the
# bounce act with the lock off, and are not greyed.
_LOCK = (settings.lock.identifier,)
DEPENDS_ON = {settings.lock_delay.identifier: (_LOCK,), settings.lock_angle.identifier: (_LOCK,)}
# What the heirloom's window can also do and this one has no use for: a command's card greyed with a switch, a
# sentence at the top of a page, a row hidden or greyed by the window's values, a picture beside the title.
COMMANDS_DEPEND_ON: dict = {}
NOTICES: dict = {}
ACTIVE_WHEN: dict = {}
SHOWN_WHEN: dict = {}
PICTURES: dict = {}
