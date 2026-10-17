"""Co-op Duel's window: DUEL, its START and STOP buttons and the score (panel_duel.py), then OPTIONS, the two keys
(panel_keys.py). Neither page holds a mods_base setting: the keys are hidden options of their own (keys.py)."""

from mods_base import NestedOption

duel = NestedOption("duel_menu", [], display_name="Duel", description="")
options = NestedOption("options_menu", [], display_name="Options", description="")
ALL = MENU = [duel, options]
