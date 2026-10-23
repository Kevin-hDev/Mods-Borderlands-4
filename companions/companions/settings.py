"""Companions' settings. The SETTINGS page's five, for every companion of the team alike (decisions 67 and 68 of
docs/renforts): health, shield, the shield's refill, speed, and the wait before coming back from a death; their
starting values, ranges and steps are spec-compagnons.md's table (« Le mod dédié »), their one authority, and the
characters' package brings any value back within its bounds (companions/tuning.py). The refill's slider starts at
NEVER: 0 on it means a broken shield never fills again. Then the bars on the left of the screen, off at first, offered
only with their package in the game (companions/bars.py). Then, hidden, the team and each hunter's outfit, kept from
one launch to the next so that the player does not make the team again at each game, and the version of what they
hold, written from the first save: a later version will know what it reads. The sliders read a file edited by hand
without ever keeping the mod from loading (slider_option.py).
"""

from mods_base import BoolOption, HiddenOption

from .slider_option import BoundedSliderOption

# The refill's slider at its left end: never filled again (spec-compagnons.md: « jamais, ou 5 à 120 s »).
NEVER = 0

health = BoundedSliderOption("health_times", 4, 1, 20, 1, True, display_name="Health",
                      description="A multiple of your hunter's health.")
shield = BoundedSliderOption("shield_percent", 30, 0, 100, 10, True, display_name="Shield",
                      description="A share of their health. 0%: no shield.")
refill = BoundedSliderOption("shield_refill_s", NEVER, NEVER, 120, 5, True, display_name="Shield refill",
                      description="The time before a broken shield comes back.")
speed = BoundedSliderOption("speed_percent", 20, 0, 50, 10, True, display_name="Speed",
                     description="On top of their own speed.")
back = BoundedSliderOption("back_after_s", 45, 10, 120, 5, True, display_name="Back after death",
                    description="They come back near you after this time.")
TEAM = [health, shield, refill, speed, back]

bars = BoolOption("companion_bars", False, display_name="Health bars on the left",
                  description="Each companion's health at the bottom left of the screen, as a teammate's in co-op.")

# The layout of the two below: a list of names, a dict of outfits by hunter.
SAVED_VERSION = 1
saved_version = HiddenOption("companions_saved_version", SAVED_VERSION)
team = HiddenOption("companions_team", [])
outfits = HiddenOption("companions_outfits", {})
HIDDEN = [saved_version, team, outfits]
