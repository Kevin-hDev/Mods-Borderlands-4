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
    description="How far the hook reaches, in centimetres. 3000 is 30 metres, the game's own outer grapple range.",
)
hook_speed = SliderOption(
    "hook_speed", 5000, 1000, 30000, step=100, is_integer=True,
    display_name="Hook speed",
    description="How fast the hook flies to the surface before the pull starts. You keep full control while it flies, "
                "so you can still jump: that is the jump grapple.",
)
# Titanfall 2 measures 1.8. Kevin settled on 1.7, and the two are not the same force: the pull is a
# multiple of the gravity of the moment, and Apex Movement doubles it, so 1.7 here is 3332 units/s²
# against Titanfall's 2700 to 3050 once converted. He wanted it slower and it is still above.
pull_strength = SliderOption(
    "pull_strength", 1.7, 0.2, 8.0, step=0.1, is_integer=False,
    display_name="Pull strength",
    description="How hard the rope pulls, as a multiple of the gravity you are under. Under 2 the rope only lifts "
                "you when you aim steeply upward; the higher it is, the flatter a shot can be and still fly you.",
)
pull_speed_cap = SliderOption(
    # Titanfall 2 adds 830 to 890 units/s, which converts to 2100 to 2550 here. Kevin first set 2000,
    # then put it back to 2500 on 2026-09-21 after comparing with the game's own grapple: "on perdait
    # trop de vitesse a 2000".
    "pull_speed_cap", 2500, 200, 8000, step=50, is_integer=True,
    display_name="Pull speed cap",
    description="How much speed the pull may add along the rope. The speed you already had is kept on top of it.",
)
steer_strength = SliderOption(
    # Twice Titanfall 2's one gravity. The reading stands, and so does this: since the mod took
    # ownership of the velocity, the stick no longer rides on the game's own air control and has the
    # whole job to do. Kevin doubled it and raised its cap by half again before the arc felt right.
    "steer_strength", 2.0, 0.0, 6.0, step=0.1, is_integer=False,
    display_name="Steering strength",
    description="How hard the move stick pushes during the pull, as a multiple of gravity. This is what bends the "
                "path: hold the stick one way and turn the camera the other to swing in an arc.",
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
    description="A quick tap gives a whole pull, even up close. Release a held key after the hook has landed "
                "to let go. Turned off, every pull runs to one of the other ends.",
)
arrival_distance = SliderOption(
    # 150 left 39 per cent of pulls running until the player hit the ground. At 600, over 380 pulls,
    # 73 per cent end at the anchor and 12 per cent on the ground. It works twice: it is the sphere
    # that counts as arrived, and three times it is how near he must have come for leaving again to
    # count as arriving.
    "arrival_distance", 600, 20, 2000, step=10, is_integer=True,
    display_name="Arrival distance",
    description="How near the anchor the pull ends, in centimetres. Capped at half the starting distance for short pulls.",
)
longest_pull = SliderOption(
    "longest_pull", 4.0, 0.0, 15.0, step=0.5, is_integer=False,
    display_name="Longest pull",
    description="How long one pull may last, in seconds. 0 means no limit. Swinging around the anchor takes far "
                "longer than flying straight at it, so a short limit cuts the swing.",
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
    description="The upward speed a pull gives you when it starts on your feet, just enough to leave the ground. "
                "The game's own jump is 840. It buys the pull the time to take hold: too little and you are "
                "back on the floor before the rope has done anything. At 0 a pull that begins standing drags you "
                "along the floor.",
)
ground_grace = SliderOption(
    "ground_grace", 0.35, 0.0, 2.0, step=0.05, is_integer=False,
    display_name="Take-off time",
    description="How long a pull ignores the ground at its start, in seconds. A pull that begins on your feet needs "
                "this much to lift you; without it the game puts you back down and the pull ends at once.",
)
release_on_landing = BoolOption(
    "release_on_landing", True,
    display_name="Let go on landing",
    description="Touching the ground ends the pull.",
)
block_jump = BoolOption(
    "block_jump", True,
    display_name="Preserve jump when detaching",
    description="Jump releases an attached grapple. Consume that press so it spends no jump; press again to jump. "
                "Turned off, the release press also goes to the game as a normal jump.",
)
melee_wins = BoolOption(
    "melee_wins", True,
    display_name="Punch wins over grapple",
    description="The grapple key is also the punch key. Aim at an enemy and you punch; aim at a surface and you "
                "grapple. Turned off, the grapple always wins and you never punch with this key.",
)
show_rope = BoolOption(
    "show_rope", True,
    display_name="Show the rope",
    description="Draw the game's own grapple beam between your hand and what you hooked, and play its arm "
                "animation. Turn it off if either of them misbehaves; the grapple itself is untouched.",
)
keep_game_grapple = BoolOption(
    "keep_game_grapple", False,
    display_name="Keep the game's grapple",
    description="The game's own grapple points still work, and this mod stands aside on them. Off, the mod takes "
                "every shot and the game's grapple never fires, which is what makes it feel like one grapple "
                "instead of two.",
)
punch_range = SliderOption(
    "punch_range", 200, 0, 1000, step=10, is_integer=True,
    display_name="Punch range",
    description="Nearby enemies and unidentified hits within this distance keep the punch, in centimetres. "
                "Known surfaces can still be grappled up close.",
)

ALL = (grapple_range, hook_speed, pull_strength, pull_speed_cap, steer_strength, steer_speed_cap,
       release_on_key_up, arrival_distance, longest_pull, rope_carry, takeoff_lift, ground_grace,
       release_on_landing,
       block_jump,
       melee_wins, keep_game_grapple, punch_range, show_rope)


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
