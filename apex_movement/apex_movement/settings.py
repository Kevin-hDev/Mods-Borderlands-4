"""Every setting of the mod, with its default and bounds; menu.py lays them out, one line per movement.

Speeds are real speeds, the ones the SDK log measures (design decision 8). The defaults keep the bare game's gap
between walk and sprint (828 - 540 = 288) and put the slide clearly above the sprint.
"""

import math

from mods_base import BoolOption, SliderOption

auto_sprint = BoolOption(
    "auto_sprint", True,
    display_name="Enabled",
    description="Sprint by pushing the move stick all the way.",
)
# The whole slide movement, on top of its own options below (Kevin's rule, 2026-09-18: every movement can be turned
# off on its own; the slides and the dash had no switch at all).
slides = BoolOption(
    "slides", True,
    display_name="Enabled",
    description="Faster, longer slides.",
)
momentum_slides = BoolOption(
    "momentum_slides", True,
    display_name="Follow momentum",
    description="Slides follow the direction you move in, not the direction you aim.",
)
dash = BoolOption(
    "dash", True,
    display_name="Enabled",
    description="A longer dash.",
)
glide = BoolOption(
    "glide", True,
    display_name="Enabled",
    description="A faster glide.",
)
# One switch for both: they share the crouch key being blocked, which is what removes the game's own held-crouch slam
# (air_crouch, 2026-09-18). The description says what comes back when it is turned off.
air_crouch = BoolOption(
    "air_crouch", True,
    display_name="Enabled",
    description="Hold crouch in the air to slide the moment you land, press jump and crouch together to slam. "
                "Turned off, the game's own crouch comes back, slam on a held crouch included.",
)
air_strafe = BoolOption(
    "air_strafe", True,
    display_name="Enabled",
    description="Change direction in the air almost at once, and start and stop faster on the ground.",
)
heavier_fall = BoolOption(
    "heavier_fall", True,
    display_name="Enabled",
    description="Fall faster without jumping any lower.",
)
# Wall climb (phase 2 spec, 2026-09-17): on by default like every Apex move but the Axle slide.
wall_climb = BoolOption(
    "wall_climb", True,
    display_name="Enabled",
    description="Climb up walls.",
)
walk_speed = SliderOption(
    "walk_speed", 672, 300, 1500, step=1, is_integer=True,
    display_name="Walk speed",
    description="The game's own value is 540.",
)
sprint_speed = SliderOption(
    "sprint_speed", 960, 300, 2000, step=1, is_integer=True,
    display_name="Sprint speed",
    description="The game's own value is 828.",
)
# 1130 after trying 1080 and 1150 in game (Kevin, 2026-09-17: "on se rapproche plus d'un apex legends"). The floor
# stays above slide_physics.STOP_SPEED (350): a slide started at or under it was ended on its first frame (review,
# 2026-09-18). test_speed_order holds that relation, since this file cannot import slide_physics.
slide_speed = SliderOption(
    "slide_speed", 1130, 400, 2500, step=1, is_integer=True,
    display_name="Slide speed",
    description="Speed a slide starts at. Never slower than the sprint speed.",
)
# Apex-style slides (Kevin, 2026-09-17): friction slows a slide, a steep enough slope cancels it, and flat ground keeps
# today's distance (1293 measured with the 1130 start, 02:05). At 2200 a straight slope of about 12 degrees keeps the
# speed; the top speed stays near the 2183 a steep slope gave with the game's own slide (01:11).
slide_distance = SliderOption(
    "slide_distance", 1300, 300, 6000, step=50, is_integer=True,
    display_name="Flat slide distance",
    description="How far a slide goes on flat ground.",
)
slide_downhill_pull = SliderOption(
    "slide_downhill_pull", 2200, 0, 6000, step=100, is_integer=True,
    display_name="Downhill pull",
    description="Slopes speed a slide up or slow it down.",
)
slide_max_speed = SliderOption(
    "slide_max_speed", 2000, 500, 4000, step=50, is_integer=True,
    display_name="Max slide speed",
    description="A slide's top speed.",
)
# Kevin, 2026-09-17: further at the game's own speed ("il faut juste qu'il aille plus loin, pas qu'il aille plus vite");
# 130 then 200 tried with the whole curve stretched, not enough, so up to 300; once only the full-speed part was
# lengthened (0.6.0), Kevin set 200 back ("on sent mieux le dash sans le bug"): 200 by default. Up to 1000, default
# kept, as players asked in the Nexus comments (Kevin, 2026-09-19); past 300 the dash goes faster, not longer (dash.py).
# The game's glide tops out at 1200 in every direction, measured on 2026-09-20. 130 % is Kevin's ask; the ceiling is
# 250 %, which is 3000, the speed of the game's own "extended" glide profile: the mod stays inside what the game ships.
glide_speed = SliderOption(
    "glide_speed", 130, 100, 250, step=5, is_integer=True,
    display_name="Glide speed",
    description="In percent. 100 is the game's speed.",
)
dash_distance = SliderOption(
    "dash_distance", 200, 100, 1000, step=5, is_integer=True,
    display_name="Dash distance",
    description="In percent. 100 is the game's dash.",
)
# Axle slide, off by default (Kevin, 2026-09-17: "c'est vraiment un move très spécifique"). Steering belongs to it
# alone: the normal slide keeps the game's own steering (Kevin: "le mode par défaut n'est pas censé pouvoir se diriger").
axle_slide = BoolOption(
    "axle_slide", False,
    display_name="Enabled",
    description="Slides you steer, and faster, as Axle's.",
)
# 350 from the steering tries (the game's 55 goes almost straight, 220 not enough, 1000, 500 and 400 tried): Kevin kept
# 350, then found it gave full control, which is the Axle slide.
axle_steering = SliderOption(
    "axle_steering", 350, 0, 1000, step=5, is_integer=True,
    display_name="Steering",
    description="How fast an Axle slide turns with the move stick, in degrees per second. The game's own value is 55.",
)
# Kevin: uphill and downhill "plus longue et plus rapide, genre dans les 25 % mais pas plus"; a slide cannot know the
# slope ahead, so the speed boost applies from the start, on any ground. Up to 50 only to compare.
axle_speed_boost = SliderOption(
    "axle_speed_boost", 25, 0, 50, step=1, is_integer=True,
    display_name="Speed boost",
    description="Extra speed, in percent.",
)
# +50 %: about 1950 on flat ground, between the longer slides Kevin liked in the lever rounds (1536 and 2464).
axle_flat_distance_boost = SliderOption(
    "axle_flat_distance_boost", 50, 0, 200, step=5, is_integer=True,
    display_name="Flat distance boost",
    description="Extra distance on flat ground, in percent.",
)
axle_slope_boost = SliderOption(
    "axle_slope_boost", 25, 0, 50, step=1, is_integer=True,
    display_name="Slope boost",
    description="Extra distance on slopes, in percent.",
)
landing_slide_min_speed = SliderOption(
    "landing_slide_min_speed", 550, 0, 2000, step=1, is_integer=True,
    display_name="Landing slide minimum speed",
    description="Arrival speed needed to slide when landing with crouch held. Never above the sprint speed.",
)

# Tuned in game by Kevin on 2026-09-17: air acceleration 24000 kept ("fonctionne nickel"), +20 jump height kept. Fall
# weight 1.6 then, raised to 2.0 on 2026-09-18 after trying 1.6, 2.0 and 2.1 in session 5 and reading Apex's own
# setting: "il faut dans les 2 pour être quasiment pareil". The top of its slider went from 2.0 to 3.0 with it, or the
# new default would sit at the top and only lighten.
air_acceleration = SliderOption(
    "air_acceleration", 24000, 2048, 32000, step=100, is_integer=True,
    display_name="Air acceleration",
    description="How fast you change direction, in the air and on the ground. The game's own value is 2048.",
)
fall_weight = SliderOption(
    "fall_weight", 2.0, 1.0, 3.0, step=0.05, is_integer=False,
    display_name="Fall weight",
    description="Strength of gravity. 1 is the game's.",
)
# Up to 1000, default kept, as players asked in the Nexus comments (Kevin, 2026-09-19). The game's standing jump rises
# 198; the description no longer says so since Kevin cut every description to what a player needs (2026-09-23).
jump_height_bonus = SliderOption(
    "jump_height_bonus", 20, 0, 1000, step=1, is_integer=True,
    display_name="Extra jump height",
    description="Extra height for every jump.",
)
# Kevin, 2026-09-17: "about twice the character's height" and a wait of "1.5 or 2 seconds" before climbing again after a
# fall. 370 climbs those 372 (the character is 186 high, measured) in about a second: a starting point, not checked
# against Apex, to tune in game.
climb_height = SliderOption(
    "climb_height", 200, 100, 400, step=10, is_integer=True,
    display_name="Climb height",
    description="In percent of your character's height.",
)
climb_speed = SliderOption(
    "climb_speed", 370, 100, 2000, step=10, is_integer=True,
    display_name="Climb speed",
    description="How fast you go up.",
)
# Kevin, 2026-09-17: "que la grimpe ne fonctionne pas que tout droit, qu'elle puisse fonctionner en diagonale jusqu'à
# 60 degrés". This one angle also opens the start and the end of a climb to the stick (climb_rules).
climb_lean = SliderOption(
    "climb_lean", 60, 0, 75, step=5, is_integer=True,
    display_name="Climb diagonal",
    description="How far a climb can go sideways.",
)
# A wait in seconds, Kevin's rule (2026-09-18): it lets a climb, then a double jump to go higher, grab the wall again
# once it is over, wherever the player is; a height rule tried that day broke that. Kevin kept 1.2 on 2026-09-17 at
# fall weight 1.6; at 1.4 and fall weight 2 he fell "beaucoup trop", where Apex grabs again "juste en dessous du niveau
# où la grimpe avait commencé". So the wait ends just after a full climb has fallen back to its start: a default climb
# rises 372 and keeps rising on its own speed, and falls back in 0.83 s at fall weight 2 (gravity 981 a second squared
# per unit of fall weight, from the 218 high jump falling in 0.527 s at 1.6, measured 2026-09-16); at 0.9 s it is about
# 90 under it, half the character. Under 0.83 the next climb starts higher and a wall is gone up for ever; at the game's
# own gravity, which Heavier Fall switched off or Apex Wall Climb alone leave, that takes 1.33 s.
reclimb_delay = SliderOption(
    "reclimb_delay", 0.9, 0.0, 3.0, step=0.1, is_integer=False,
    display_name="Climb again after",
    description="Wait before you can climb again. Touching the ground clears it.",
)


# How long the game is told a slide may last: only a far safety net, since slides end when the mod ends them. It lives
# here rather than in slide_physics because the landing slide's own safety net has to outlast it, and that belongs to
# another movement (2026-09-18): one value, one place, read by both.
LONGEST_SLIDE_S = 30.0


def keep_in_bounds() -> list[str]:
    """Brings every slider back within its own bounds, and a value that is not a number back to its default.

    mods_base loads a slider from the settings file without its bounds, and keeps NaN (review, 2026-09-19): a file
    edited by hand asked for a 20 s dash, no gravity, or a slide flung at 100000. Run when the mod is switched on,
    once the file is loaded, and at every frame of the player: the console menu does not hold a slider to its bounds
    either (Vehicle Driving, 2026-09-19: 250 typed for a slider shown [100-200] was taken).
    """
    told: list[str] = []
    for option in list(globals().values()):
        if not isinstance(option, SliderOption) or getattr(option, "min_value", None) is None:
            continue
        value = float(option.value)
        kept = min(option.max_value, max(option.min_value, value)) if math.isfinite(value) else option.default_value
        if kept != value:
            told.append(f"setting {option.identifier}={option.value} outside {option.min_value}-{option.max_value}, "
                        f"set to {kept}")
            option.value = kept
    return told
