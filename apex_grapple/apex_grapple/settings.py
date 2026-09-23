"""Every setting of the mod, with its default and its bounds; menu.py lays them out.

The mod is one movement, so it has no switch of its own: turning the mod off in the mods list is
the switch (Kevin's rule, 2026-09-18, one mod is one movement).

The defaults are **Kevin's**, set by hand in game over an hour and 380 pulls on 2026-09-20, and kept
because he is the one who has played six years of Apex Legends: "c'est ce qui se rapproche le plus
d'Apex Legends selon moi". Where they differ from the Titanfall 2 readings the comment above each
one says by how much, since the difference is itself a finding.

The Titanfall 2 conversions they came from: the forces convert by gravity, the speeds by the running
speed of each game — 260 units/s there, 750 here. Both are written down in
docs/candidats/grappin.md.
"""

import math

from mods_base import BoolOption, SliderOption

grapple_range = SliderOption(
    "grapple_range", 3000, 500, 10000, step=50, is_integer=True,
    display_name="Range",
    description="How far the hook reaches. 3000 is 30 metres.",
)
hook_speed = SliderOption(
    "hook_speed", 5000, 1000, 30000, step=100, is_integer=True,
    display_name="Hook speed",
    description="How fast the hook flies to its target.",
)
# Titanfall 2 measures 1.8. Kevin settled on 1.7, and the two are not the same force: the pull is a
# multiple of the gravity of the moment, and Apex Movement doubles it, so 1.7 here is 3332 units/s²
# against Titanfall's 2700 to 3050 once converted. He wanted it slower and it is still above.
pull_strength = SliderOption(
    "pull_strength", 1.7, 0.2, 8.0, step=0.1, is_integer=False,
    display_name="Pull strength",
    description="How hard the rope pulls you.",
)
pull_speed_cap = SliderOption(
    # Titanfall 2 adds 830 to 890 units/s, which converts to 2100 to 2550 here. Kevin first set 2000,
    # then put it back to 2500 on 2026-09-21 after comparing with the game's own grapple: "on perdait
    # trop de vitesse a 2000".
    "pull_speed_cap", 2500, 200, 8000, step=50, is_integer=True,
    display_name="Pull speed cap",
    description="Top speed the rope gives. Your momentum adds to it.",
)
steer_strength = SliderOption(
    # Twice Titanfall 2's one gravity. The reading stands, and so does this: since the mod took
    # ownership of the velocity, the stick no longer rides on the game's own air control and has the
    # whole job to do. Kevin doubled it and raised its cap by half again before the arc felt right.
    "steer_strength", 2.0, 0.0, 6.0, step=0.1, is_integer=False,
    display_name="Steering strength",
    description="How much the move stick bends your path.",
)
steer_speed_cap = SliderOption(
    "steer_speed_cap", 1000, 0, 3000, step=25, is_integer=True,
    display_name="Steering speed cap",
    description="How much sideways speed the move stick may reach during a pull. Well under the pull cap, as in "
                "Titanfall 2, or steering would outrun the rope.",
)
release_on_key_up = BoolOption(
    "release_on_key_up", True,
    display_name="Hold to keep pulling",
    description="Releasing the key lets go. A quick tap pulls all the way.",
)
arrival_distance = SliderOption(
    # 150 left 39 per cent of pulls running until the player hit the ground. At 600, over 380 pulls,
    # 73 per cent end at the anchor and 12 per cent on the ground. It works twice: it is the sphere
    # that counts as arrived, and three times it is how near he must have come for leaving again to
    # count as arriving.
    "arrival_distance", 600, 20, 2000, step=10, is_integer=True,
    display_name="Arrival distance",
    description="The pull stops this far from the anchor.",
)
longest_pull = SliderOption(
    "longest_pull", 4.0, 0.0, 15.0, step=0.5, is_integer=False,
    display_name="Longest pull",
    description="In seconds. 0 means no limit.",
)
rope_carry = SliderOption(
    "rope_carry", 100, 0, 100, step=5, is_integer=True,
    display_name="Rope carries you",
    description="How much of your weight the rope holds while the hook is set, as a percentage. At 100 you fly "
                "straight where you aimed and fall only once you let go, as in Apex. At 0 you fall the whole way, "
                "and a shot level with your eyes meets the floor a third of the way there.",
)
takeoff_lift = SliderOption(
    "takeoff_lift", 250, 0, 1500, step=25, is_integer=True,
    display_name="Take-off lift",
    description="A small hop when a pull starts on the ground. At 0 you leave along the floor.",
)
ground_grace = SliderOption(
    "ground_grace", 0.35, 0.0, 2.0, step=0.05, is_integer=False,
    display_name="Take-off time",
    description="The ground is ignored this long at the start, so you can take off.",
)
release_on_landing = BoolOption(
    "release_on_landing", True,
    display_name="Let go on landing",
    description="Touching the ground ends the pull.",
)
block_jump = BoolOption(
    "block_jump", True,
    display_name="Preserve jump when detaching",
    description="Jumping to let go spends no jump.",
)
melee_wins = BoolOption(
    "melee_wins", True,
    display_name="Punch wins over grapple",
    description="On an enemy, the key punches instead of grappling.",
)
show_rope = BoolOption(
    "show_rope", True,
    display_name="Show the rope",
    description="Show the rope and the arm animation.",
)
keep_game_grapple = BoolOption(
    "keep_game_grapple", False,
    display_name="Keep the game's grapple",
    description="The game's grapple points keep the game's own grapple.",
)
punch_range = SliderOption(
    "punch_range", 200, 0, 1000, step=10, is_integer=True,
    display_name="Punch range",
    description="An enemy closer than this gets punched.",
)

# The reserve the dash and the glide already spend, measured on 2026-09-22: full at 100, a dash takes
# half of it, and the game refills it 3.2 s later at about a quarter a second. Kevin set three shots
# on a full bar (2026-09-22): "33% par defaut pour en avoir trois".
stamina_cost = SliderOption(
    "stamina_cost", 33, 0, 100, step=1, is_integer=True,
    display_name="Stamina cost",
    description="Share of the stamina bar each shot spends. 33 is three shots, 0 is free.",
)

ALL = (grapple_range, hook_speed, pull_strength, pull_speed_cap, steer_strength, steer_speed_cap,
       release_on_key_up, arrival_distance, longest_pull, rope_carry, takeoff_lift, ground_grace,
       release_on_landing,
       block_jump,
       melee_wins, keep_game_grapple, punch_range, show_rope, stamina_cost)


def summary() -> str:
    """Every setting and the value actually in use, for the log at switch-on.

    Written because a default changed in the sources is not the value the game runs: mods_base loads
    the player's settings file over it, and a whole session was read on 2026-09-20 as if two new
    defaults had applied when the saved file still held the old ones.
    """
    return ", ".join(f"{option.identifier}={option.value}" for option in ALL)


def keep_in_bounds() -> list[str]:
    """Validate loaded/menu values before physics, then enforce relationships.

    The SDK does not enforce slider bounds or reject NaN when loading settings.
    Defaults and bounds belong to the options; valid values keep their precision.
    """
    # ALL is fixed: at most one warning per option plus the range relationship.
    warnings: list[str] = []
    for option in ALL:
        value = option.value
        if type(option.default_value) is bool:
            if type(value) is bool:
                continue
            kept = option.default_value
        elif type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            # Do not treat bool as 0/1 or coerce strings; malformed settings use their default.
            kept = option.default_value
        else:
            # Compare integers directly: float() can overflow for edited, very large integers.
            if option.min_value <= value <= option.max_value:
                continue
            kept = min(option.max_value, max(option.min_value, value))
        option.value = kept
        # Never echo external values: they may be arbitrary text rather than numbers.
        warnings.append(f"invalid {option.identifier.replace('_', ' ')} setting; set to {kept}")
    if punch_range.value >= grapple_range.value:
        punch_range.value = max(punch_range.min_value, grapple_range.value - 100)
        warnings.append(f"punch range must stay under the grapple range; set to {punch_range.value}")
    return warnings
