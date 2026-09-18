"""Every setting of the mod, with its default and bounds; menu.py lays them out, one line per movement.

Speeds are real speeds, the ones the SDK log measures (design decision 8). The defaults keep the bare game's gap
between walk and sprint (828 - 540 = 288) and put the slide clearly above the sprint.
"""

from dataclasses import dataclass

from mods_base import BoolOption, SliderOption

auto_sprint = BoolOption(
    "auto_sprint", True,
    display_name="Enabled",
    description="Sprint as soon as the move stick is fully pushed, up to the game's own 60 degree limit.",
)
# The whole slide movement, on top of its own options below (Kevin's rule, 2026-09-18: every movement can be turned
# off on its own; the slides and the dash had no switch at all).
slides = BoolOption(
    "slides", True,
    display_name="Enabled",
    description="Faster, longer slides. Turned off, slides are the game's own again.",
)
momentum_slides = BoolOption(
    "momentum_slides", True,
    display_name="Follow momentum",
    description="Slides follow the direction you move in, not the direction you aim.",
)
dash = BoolOption(
    "dash", True,
    display_name="Enabled",
    description="A longer dash. Turned off, the dash is the game's own again.",
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
    description="Fall faster after a jump or a drop; every jump keeps its height.",
)
# Wall climb (phase 2 spec, 2026-09-17): on by default like every Apex move but the Axle slide.
wall_climb = BoolOption(
    "wall_climb", True,
    display_name="Enabled",
    description="Jump at a wall with the move stick pushed toward it and look at it: you climb up it, straight or diagonally, and pull yourself over the top.",
)
walk_speed = SliderOption(
    "walk_speed", 672, 300, 1500, step=1, is_integer=True,
    display_name="Walk speed",
    description="Ground speed while walking. The game's own value is 540.",
)
sprint_speed = SliderOption(
    "sprint_speed", 960, 300, 2000, step=1, is_integer=True,
    display_name="Sprint speed",
    description="Ground speed while sprinting, never slower than the walk speed. The game's own value is 828.",
)
# 1130 after trying 1080 and 1150 in game (Kevin, 2026-09-17: "on se rapproche plus d'un apex legends").
slide_speed = SliderOption(
    "slide_speed", 1130, 300, 2500, step=1, is_integer=True,
    display_name="Slide speed",
    description="Speed a slide starts at. Never slower than the sprint speed.",
)
# Apex-style slides (Kevin, 2026-09-17): friction slows a slide, a steep enough slope cancels it, and flat ground keeps
# today's distance (1293 measured with the 1130 start, 02:05). At 2200 a straight slope of about 12 degrees keeps the
# speed; the top speed stays near the 2183 a steep slope gave with the game's own slide (01:11).
slide_distance = SliderOption(
    "slide_distance", 1300, 300, 6000, step=50, is_integer=True,
    display_name="Flat slide distance",
    description="How far a slide goes on flat ground. Slopes add to it downhill and take from it uphill.",
)
slide_downhill_pull = SliderOption(
    "slide_downhill_pull", 2200, 0, 6000, step=100, is_integer=True,
    display_name="Downhill pull",
    description="How strongly slopes speed a slide up or slow it down. At 2200 a slope of about 12 degrees keeps its speed.",
)
slide_max_speed = SliderOption(
    "slide_max_speed", 2000, 500, 4000, step=50, is_integer=True,
    display_name="Max slide speed",
    description="A slide never goes faster than this, however steep the slope.",
)
# Kevin, 2026-09-17: further at the game's own speed ("il faut juste qu'il aille plus loin, pas qu'il aille plus vite");
# 130 then 200 tried with the whole curve stretched, not enough, so up to 300; once only the full-speed part was
# lengthened (0.6.0), Kevin set 200 back ("on sent mieux le dash sans le bug"): 200 by default.
dash_distance = SliderOption(
    "dash_distance", 200, 100, 300, step=5, is_integer=True,
    display_name="Dash distance",
    description="Percent of the game's dash distance. The dash lasts longer at the game's own speed. 100 is the game.",
)
# Axle slide, off by default (Kevin, 2026-09-17: "c'est vraiment un move très spécifique"). Steering belongs to it
# alone: the normal slide keeps the game's own steering (Kevin: "le mode par défaut n'est pas censé pouvoir se diriger").
axle_slide = BoolOption(
    "axle_slide", False,
    display_name="Enabled",
    description="Slides as Axle's in Apex Legends: steered with the move stick, and boosted every time.",
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
    description="Percent faster than a normal slide: its start and its top speed.",
)
# +50 %: about 1950 on flat ground, between the longer slides Kevin liked in the lever rounds (1536 and 2464).
axle_flat_distance_boost = SliderOption(
    "axle_flat_distance_boost", 50, 0, 200, step=5, is_integer=True,
    display_name="Flat distance boost",
    description="Percent further than a normal slide on flat ground.",
)
axle_slope_boost = SliderOption(
    "axle_slope_boost", 25, 0, 50, step=1, is_integer=True,
    display_name="Slope boost",
    description="Percent further than a normal slide on the same slope, uphill and downhill.",
)
landing_slide_min_speed = SliderOption(
    "landing_slide_min_speed", 550, 0, 2000, step=1, is_integer=True,
    display_name="Landing slide minimum speed",
    description="Arrival speed needed to slide when landing with crouch held. Never above the sprint speed.",
)

# Tuned in game by Kevin on 2026-09-17: fall weight 1.3, 1.5, 1.7 then 1.6 kept ("1.6 c'est la bonne avec la hauteur
# actuelle"), air acceleration 24000 kept ("fonctionne nickel"), +20 jump height kept.
air_acceleration = SliderOption(
    "air_acceleration", 24000, 2048, 32000, step=100, is_integer=True,
    display_name="Air acceleration",
    description="How fast you change direction, in the air and on the ground. The game's own value is 2048.",
)
fall_weight = SliderOption(
    "fall_weight", 1.6, 1.0, 2.0, step=0.05, is_integer=False,
    display_name="Fall weight",
    description="Gravity multiplier. Jumps keep their height; only the time in the air gets shorter. 1.0 is the game.",
)
jump_height_bonus = SliderOption(
    "jump_height_bonus", 20, 0, 100, step=1, is_integer=True,
    display_name="Extra jump height",
    description="Added to every jump: standing, sprint, double, slide and ladder jumps.",
)
# Kevin, 2026-09-17: "about twice the character's height" and a wait of "1.5 or 2 seconds" before climbing again after a
# fall. 370 climbs those 372 (the character is 186 high, measured) in about a second: a starting point, not checked
# against Apex, to tune in game.
climb_height = SliderOption(
    "climb_height", 200, 100, 400, step=10, is_integer=True,
    display_name="Climb height",
    description="How high a climb goes, in percent of your character's height.",
)
climb_speed = SliderOption(
    "climb_speed", 370, 100, 2000, step=10, is_integer=True,
    display_name="Climb speed",
    description="How fast you climb.",
)
# Kevin, 2026-09-17: "que la grimpe ne fonctionne pas que tout droit, qu'elle puisse fonctionner en diagonale jusqu'à
# 60 degrés". This one angle also opens the start and the end of a climb to the stick (climb_rules).
climb_lean = SliderOption(
    "climb_lean", 60, 0, 75, step=5, is_integer=True,
    display_name="Climb diagonal",
    description="How far a climb follows the move stick to a side, in degrees. At 0 you only climb straight up.",
)
# Kevin asked for a shorter wait on 2026-09-17, closer to Apex, and kept 1.2 after trying it in game. It also stays
# above the point where a wall can be gone up for ever: a default climb rises 372, keeps 44 more of its own speed, and
# needs 0.96 s to fall back to where it started (gravity 1570 a second squared, from the 218 high jump falling in
# 0.527 s at fall weight 1.6, measured 2026-09-16). Under that the next climb starts higher than the last one began.
reclimb_delay = SliderOption(
    "reclimb_delay", 1.2, 0.0, 3.0, step=0.1, is_integer=False,
    display_name="Climb again after",
    description="Seconds before you can climb again after a climb that did not reach the top. Landing clears it.",
)


# How long the game is told a slide may last: only a far safety net, since slides end when the mod ends them. It lives
# here rather than in slide_physics because the landing slide's own safety net has to outlast it, and that belongs to
# another movement (2026-09-18): one value, one place, read by both.
LONGEST_SLIDE_S = 30.0


@dataclass(frozen=True)
class Speeds:
    walk: float
    sprint: float
    slide: float
    landing_slide_min: float


def ordered(walk: float, sprint: float, slide: float, landing_slide_min: float) -> Speeds:
    """Keeps walk <= sprint <= slide and the landing slide minimum <= sprint, whatever the sliders say.

    A slider cannot take another slider as its bound, so the order Kevin set (design decision 9) is enforced here.
    """
    sprint = max(sprint, walk)
    return Speeds(walk=walk, sprint=sprint, slide=max(slide, sprint), landing_slide_min=min(landing_slide_min, sprint))


def speeds() -> Speeds:
    return ordered(
        float(walk_speed.value), float(sprint_speed.value), float(slide_speed.value),
        float(landing_slide_min_speed.value),
    )
