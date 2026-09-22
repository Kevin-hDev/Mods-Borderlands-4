"""Tests the settings: their defaults are the measured ones, and two that cannot hold together are put right."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


# Kevin's own values, set in game over an hour and 380 pulls on 2026-09-20 and kept as the defaults.
# Written here so that changing one by accident shows up in a test and not in his hands.
check("the pull is the 1.7 Kevin settled on", settings.pull_strength.default_value == 1.7)
# Put back to 2500 on 2026-09-21: at 2000 the mod lost too much speed against the game's own grapple.
check("the pull cap is his 2500", settings.pull_speed_cap.default_value == 2500)
check("the steering is his 2.0, twice what Titanfall 2 measured",
      settings.steer_strength.default_value == 2.0)
check("its cap is his 1000", settings.steer_speed_cap.default_value == 1000)
check("the arrival distance is his 600, which ended 73 per cent of pulls at the anchor",
      settings.arrival_distance.default_value == 600)
check("the take-off lift is his 250", settings.takeoff_lift.default_value == 250)
# That ratio only works because the rope carries the weight. Left to fall, a pull at 1.8 lifts a
# player from no rope shallower than 34 degrees, and every rope measured in game was under 32.
check("the rope carries the whole weight by default",
      settings.rope_carry.default_value == 100)
check("without it, the pull would ask for a rope steeper than 30 degrees",
      math.degrees(math.asin(1.0 / settings.pull_strength.default_value)) > 30.0)
check("steering stays under the pull, as it was measured, though less far under than in Titanfall 2",
      settings.steer_speed_cap.default_value < settings.pull_speed_cap.default_value)
check("the range is the 30 metres Kevin asked for", settings.grapple_range.default_value == 3000)

check("every setting is in the list the menu draws from", len(settings.ALL) == 19)
check("the take-off time is long enough to leave the ground, which 0.06 s was not",
      settings.ground_grace.default_value >= 0.2)
check("the lift is under the game's own jump of 840: leaving the floor, not jumping",
      0 < settings.takeoff_lift.default_value < 840)
check("each of them is there once", len({option.identifier for option in settings.ALL}) == len(settings.ALL))
check("every setting has a name a player can read",
      all(option.display_name and option.display_name != option.identifier for option in settings.ALL))

# Kevin's rule, 2026-09-20: the game's grapple is off by default and the player turns it back on.
check("the game's own grapple is off by default", settings.keep_game_grapple.default_value is False)
check("the rope is shown by default", settings.show_rope.default_value is True)

check("as they stand, the settings hold together", settings.keep_in_bounds() == [])

# The arrival distance has to be able to hold 600, which the first bounds stopped at 1000.
settings.arrival_distance.value = settings.arrival_distance.max_value
check("the arrival distance goes well past Kevin's 600", settings.arrival_distance.value >= 1000)
settings.arrival_distance.value = settings.arrival_distance.default_value

settings.punch_range.value = 5000
settings.grapple_range.value = 3000
warnings = settings.keep_in_bounds()
check("a punch range past the grapple range is put right", settings.punch_range.value < 3000)
check("and it is said, rather than changed in silence", warnings and "punch range" in warnings[0])
check("nothing is left out of bounds afterwards", settings.keep_in_bounds() == [])

settings.punch_range.value = settings.punch_range.default_value
settings.grapple_range.value = settings.grapple_range.default_value

# A default changed in the sources is not what the game runs: the player's settings file wins, and a
# whole session was once read as if two new defaults had applied when the saved file held the old ones.
told = settings.summary()
check("the log line names every setting", all(option.identifier in told for option in settings.ALL))
settings.pull_strength.value = 4.2
check("and gives the value in use, not the default", "pull_strength=4.2" in settings.summary())
settings.pull_strength.value = settings.pull_strength.default_value

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
