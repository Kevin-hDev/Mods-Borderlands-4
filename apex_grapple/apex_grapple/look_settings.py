"""The grapple gun's look: its settings, on the window's LOOK page with "Show the rope" (Kevin, 2026-10-14, sketch A,
docs/apex_grapple/pistolet-grappin/apercus/2026-10-14-reglages/, decisions.md of that dossier).

Each value is the letter of the drawing Kevin chose it on, or the colour's name, the key look_assets and rope_motion
use, so that one name means one thing everywhere; the window's words for them are its own (panel_en.py, panel_fr.py,
panel_zh.py). Each default is the look's first: look_assets for what the build and the drawings chose, rope_motion for
the movement.
"""

from mods_base import SpinnerOption

from . import look_assets, rope_motion

GRAPPLE_GUN, CLASSIC = "GRAPPLE_GUN", "CLASSIC"

look = SpinnerOption(
    "look", GRAPPLE_GUN, [GRAPPLE_GUN, CLASSIC],
    display_name="Look",
    description="Grapple gun: our gun, rope and hook. Classic: the game's gesture and rope.",
)
rope_look = SpinnerOption(
    "rope_look", look_assets.ROPE["look_at_first"], list(look_assets.ROPE["pieces"]),
    display_name="Rope",
    description="Thread: a thread of light wound round it. Core: the light between its strands. Glow: a glow round it.",
)
rope_thickness = SpinnerOption(
    "rope_thickness", look_assets.ROPE["thickness_at_first"], list(look_assets.ROPE["thicknesses_cm"]),
    display_name="Thickness",
    description="How thick the rope is.",
)
rope_light = SpinnerOption(
    "rope_light", look_assets.ROPE_LIGHT_AT_FIRST, list(look_assets.ROPE_LIGHTS),
    display_name="Light",
    description="How strong the rope's light is.",
)
rope_colour = SpinnerOption(
    "rope_colour", look_assets.COLOUR_AT_FIRST, list(look_assets.COLOURS),
    display_name="Light colour",
    description="The colour of the rope's light.",
)
glow_face = SpinnerOption(
    "glow_face", look_assets.ROPE_FACE_AT_FIRST, list(look_assets.ROPE_FACES),
    display_name="Glow face",
    description="With the glow, how much the rope itself lights up.",
)
rope_movement = SpinnerOption(
    "rope_movement", rope_motion.SLACK_CHOSEN, list(rope_motion.SLACKS),
    display_name="Rope movement",
    description="How much the rope hangs and waves as the hook flies out and back.",
)
hook_size = SpinnerOption(
    "hook_size", look_assets.HOOK_SIZE_AT_FIRST, list(look_assets.HOOK_SIZES),
    display_name="Hook size",
    description="The size of the hook in the wall.",
)
# Kevin's sketch of the page, validated on 14 October (conception-pistolet-et-gestes.md): with the holster at first.
WITH, WITHOUT = "WITH", "WITHOUT"
holster = SpinnerOption(
    "holster", WITH, [WITH, WITHOUT],
    display_name="Holster in third person",
    description="In third person, the hunter wears the grapple gun's holster on the hip.",
)

# The game's rope in the same colours, its own blue at first (decisions.md, 14 October).
game_rope_colour = SpinnerOption(
    "game_rope_colour", look_assets.GAME_COLOUR_AT_FIRST, list(look_assets.COLOURS),
    display_name="Game rope colour",
    description="The colour of the game's rope, with the classic look.",
)

# In the sketch's order (decisions.md, 14 October, « une page APPARENCE »).
ALL = (look, rope_look, glow_face, rope_thickness, rope_light, rope_colour, rope_movement, hook_size, holster,
       game_rope_colour)
# The rows that change nothing with the classic look: they grey on the LOOK page (spec-pistolet-grappin.md, section 9,
# choice 2).
OURS_ONLY = (rope_look, glow_face, rope_thickness, rope_light, rope_colour, rope_movement, hook_size, holster)
