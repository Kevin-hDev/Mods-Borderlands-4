"""Design authority for the settings window: the tokens of Kevin's approved mockup v2, in CSS pixels.

outils/export_menu_tokens.py writes the mockup's tokens.css from this file. On 2026-09-21 the values had been
copied by hand into the mod, drifted, and Kevin saw a different window in game than the one he approved.
Names follow the mockup's CSS variables: COLOR_GOLD is --color-gold.
"""

from . import menu, pack

# Colours, sRGB hex as in the mockup: black, ember red, orange and yellow from Kevin's reference image.
COLOR_WINDOW = "1e0906"
COLOR_HEADER = "2b0c07"
COLOR_SIDEBAR = "140605"
COLOR_CARD = "120504"
COLOR_HOVER = "3d1109"
COLOR_SPARK = "ff7a1a"
COLOR_GOLD = "ffd21f"
COLOR_GOLD_HI = "ffe45c"
COLOR_GOLD_SHADE = "5a3a00"
COLOR_TEXT = "f6ead6"
COLOR_TEXT_DIM = "b09274"
COLOR_TRACK = "3a120c"
COLOR_INK = "000000"
OPACITY_DISABLED = 0.35

# Type: Anton for titles (closest free font to the Borderlands logo), Barlow Condensed for the rest.
WEIGHT_REGULAR = 500
WEIGHT_MEDIUM = 600
WEIGHT_BOLD = 800
TEXT_2XS = 15
TEXT_XS = 17
TEXT_SM = 18
TEXT_MD = 20
TEXT_LG = 24
TEXT_HERO = 58
TEXT_LOGO = 64
TRACKING_SM = 0.5
TRACKING_MD = 1
TRACKING_LG = 1.5
TRACKING_XL = 3
LEADING_NONE = 1
LEADING_TIGHT = 1.05
LEADING_SNUG = 1.15
LEADING_BODY = 1.3

# Ink: the comic-book black outline and hard offset shadow.
STROKE_THIN = 2
STROKE = 3
STROKE_THICK = 4
TEXT_STROKE = 7
SHADOW_SM = 3
SHADOW_MD = 5
SHADOW_LG = 7
SHADOW_XL = 14

# Shapes, in degrees for the angles.
RADIUS_SM = 4
RADIUS_MD = 6
SLANT = -12
TILT_LOGO = -3
TILT_TITLE = -2
HAZARD_ANGLE = -45
HAZARD_STRIPE = 18
HAZARD_HEIGHT = 14
# Conflict warning, drawn in the mockup of 2026-09-22 and not in game yet: an orange square turned into a diamond
# behind a "!", on a sidebar line and on the Conflicts tab. Its shape, not only its colour, sets it apart.
TILT_WARNING = 45
WARNING_SIZE = 18

SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 20
SPACE_6 = 24
SPACE_7 = 28
SPACE_8 = 36
SPACE_9 = 48

# Layout on the 1920 × 1080 reference screen; the window scales with the screen from there.
STAGE_WIDTH = 1920
STAGE_HEIGHT = 1080
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 830
HEADER_HEIGHT = 96
AVATAR_SIZE = 72
SIDEBAR_WIDTH = 340
ROW_LABEL_WIDTH = 330
ROW_VALUE_WIDTH = 120
DESC_MAX_WIDTH = 720
SCROLLBAR_WIDTH = 14
STATE_WIDTH = 48
SWITCH_WIDTH = 96
MASTER_WIDTH = 150
SLIDER_HEIGHT = 34
SLIDER_TRACK = 16
SLIDER_THUMB_WIDTH = 18
SLIDER_THUMB_HEIGHT = 34

# Game-only values, not design tokens: the exporter skips names that start with an underscore or are listed here.
GAME_ONLY = ("ORDER", "SAVE_DELAY_NS", "PAGES", "BRAND", "AUTHOR", "PX_TO_POINTS", "SPARKS", "HOVER_OVERLAY",
             "PRESS_OVERLAY", "SELECTOR_WIDTH", "FONT_LINE_HEIGHT", "GAME_ONLY")
ORDER = 10000
SAVE_DELAY_NS = 300_000_000
PAGES = tuple(group.identifier.removesuffix("_menu") for group in menu.MENU)
BRAND, AUTHOR = pack.NAME.upper(), "KEVIN-HDEV"
# Unreal sizes fonts in points drawn at 96 DPI: a size of 20 is 26.7 pixels. The mockup's pixels times 0.75 give
# the same letters; without it every text was a third larger than approved (screenshot of 2026-09-21).
PX_TO_POINTS = 0.75
# Line height of each shipped font, in em, read from the files' hhea tables (2026-09-21). Unreal always lays a line
# out at this height, where the mockup's CSS squeezes Anton to 1.15: panel_text trims the difference from paddings.
FONT_LINE_HEIGHT = {"title": 1.505, "body": 1.2}
# The key-capture buttons, absent from the mockup: wide enough for "2. CHOISIR LA DEUXIÈME TOUCHE".
SELECTOR_WIDTH = 420
KEY_ICON_SIZE = 40
# The mockup lightens a hovered button and darkens a pressed one; one veil does both for every button colour.
HOVER_OVERLAY = ("ffffff", 0.12)
PRESS_OVERLAY = ("000000", 0.2)
# The mockup's header sparks: (left, top, side, colour, opacity), fixed so every opening looks the same.
SPARKS = (
    (300, 18, 5, COLOR_SPARK, 0.9), (340, 62, 3, COLOR_GOLD, 0.8), (420, 30, 4, COLOR_SPARK, 0.6),
    (480, 70, 3, COLOR_GOLD, 0.7), (560, 14, 3, COLOR_SPARK, 0.5), (640, 52, 5, COLOR_GOLD, 0.45),
    (720, 24, 3, COLOR_SPARK, 0.4), (820, 66, 4, COLOR_SPARK, 0.35), (900, 20, 3, COLOR_GOLD, 0.3),
    (1000, 48, 3, COLOR_SPARK, 0.25), (1120, 72, 4, COLOR_GOLD, 0.25), (1180, 16, 3, COLOR_SPARK, 0.3),
    (40, 78, 3, COLOR_GOLD, 0.5), (120, 10, 4, COLOR_SPARK, 0.6), (230, 80, 3, COLOR_SPARK, 0.7),
)


def rgba(hex_color, alpha=1.0):
    # Unreal colours are linear; converting from sRGB keeps the mockup's dark reds dark.
    values = tuple(int(hex_color[index:index + 2], 16) / 255 for index in (0, 2, 4))
    return tuple(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                 for value in values) + (alpha,)


def points(pixels):
    return pixels * PX_TO_POINTS
