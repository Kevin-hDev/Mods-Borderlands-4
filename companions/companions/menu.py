"""Companions' window, sketch A of esquisses_mod_companions, chosen by Kevin (decision 68 of docs/renforts): its pages
VAULT HUNTERS and ALLIES, the companions' cards (panel_cards.py), and SETTINGS, the team's five settings, then the
bars on the left of the screen and the two keys (panel_settings.py). The window draws each page through panel_team.py.
A card page holds no setting of the SDK's: the team and the outfits are hidden settings written at a click
(team_choices.py)."""

from mods_base import NestedOption

from . import settings

hunters = NestedOption("hunters_menu", [], display_name="Vault Hunters",
                       description="The Vault Hunters fight with their weapons only, not their skills.")
allies = NestedOption("allies_menu", [], display_name="Allies", description="")
team = NestedOption("settings_menu", [*settings.TEAM, settings.bars], display_name="Settings",
                    description="For all your companions.")
ALL = MENU = [hunters, allies, team]
