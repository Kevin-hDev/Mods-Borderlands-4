"""Hunter Change's two pages for its window, and the picture of each hunter card. The pages hold no mods_base option:
the look is each game's own (choices.py), chosen on the APPEARANCE page's cards (panel_hunters.py); the hunter is each
save's own, changed on the HUNTER page's cards (panel_switch.py)."""

from mods_base import NestedOption

from . import hunters, panel_hunters_theme as ht

appearance = NestedOption(
    "appearance_menu", [], display_name="Appearance",
    description="Wear another hunter's look. You keep your own skills, level and skill tree.",
)
hunter = NestedOption(
    "hunter_menu", [], display_name="Hunter",
    description="Become another hunter in this game.",
)

ALL = MENU = [appearance, hunter]

# Each card's face: its file in assets/, then its width and height in the window's units (panel_assets loads them).
PICTURES = {hunter.code: (f"hunter_{hunter.code}.png", ht.PICTURE_SIZE, ht.PICTURE_SIZE) for hunter in hunters.HUNTERS}
