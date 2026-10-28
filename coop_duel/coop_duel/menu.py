"""Co-op Duel's window: DUEL, its START and STOP buttons and the score (panel_duel.py), TEAMS, each player's team
(panel_teams.py), then OPTIONS, the two keys (panel_keys.py). No page holds a mods_base setting: the keys are hidden
options of their own (keys.py), the teams live for the session (roster.py)."""

from mods_base import NestedOption

duel = NestedOption("duel_menu", [], display_name="Duel", description="")
teams = NestedOption("teams_menu", [], display_name="Teams", description="")
options = NestedOption("options_menu", [], display_name="Options", description="")
ALL = MENU = [duel, teams, options]
