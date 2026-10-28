"""What the player sets for the heirloom: whether it shows, which heirloom, the skin and size of each, the glow's force,
the mode, and the draw's start and speed. Each applies from the next weapon change (Kevin, 2026-09-26,
docs/mokup/menu_mods/decisions.md): the game reads the hands' animations only then, and the heirloom changes with them;
a skin or a force shows at once on the heirloom in hand (heirloom_choices.py).

Why these, 2026-09-25 (cosmetics/heirloom/docs/heirloom.md, section 17): the settings are the players', not the
tester's. The switch came when Tidy Weapons joined the heirloom (Kevin, 2026-09-26: « un interrupteur par partie »):
the mod's own switch turns both parts off, this one the heirloom alone, for a player who puts the weapon away with
another mod. Why a choice of heirloom, 2026-09-29 (same decisions, sketch H2): Kevin chose that the menu offers the
knife and the axe, each with its own animations, skins and glow, each keeping its own size (sketch K1); each keeps its
own skin too, so that going back to one finds it as it was left. These options are the choice's one authority: saved
with the others and read here, where a value a hand-edited file breaks reads as the default.
"""

from typing import Any

from mods_base import BoolOption, SliderOption, SpinnerOption

from .apex_anim_list import DEFAULT_MODE, MODES as LIST_MODES
from .apex_fit import Fit
from .heirloom_catalog import DEFAULT, HEIRLOOMS, OFFERED
from .apex_moves_timing import LIMITS, Timing
from .slider_values import bounded

# The menu names each mode; its list is named in lower case (heirloom.json, "lists").
MODES = {name.capitalize(): name for name in LIST_MODES}
# 100 % is each heirloom's size as Kevin validated it (its hold's, heirloom_catalog.py): the knife's is 62 % of the
# game's knife.
SIZE_PERCENT = (50, 150)
# The knife's size keeps the name it was saved under when the knife was the only heirloom (1.0.0): a player finds
# theirs.
SAVED_SIZE = {"jakobs_knife": "size"}
# The glow's forces, 1 to 5, 3 by default, for every heirloom that glows (Kevin, 2026-09-28 and 29,
# docs/mokup/menu_mods/decisions.md); each heirloom sets its strength at each (its skin's "glow").
FORCES = 5
DEFAULT_FORCE = 3
# Each heirloom's own look comes first among its skins.
OWN_SKIN = "own"
DRAW_STEP = 0.05

heirloom = BoolOption(
    "heirloom", True, display_name="Heirloom",
    description="No: your hands stay empty when your weapon is put away, as in the game.",
)
model = SpinnerOption("model", DEFAULT, list(OFFERED), display_name="Model", description="The heirloom you hold.")
# One row per heirloom; the window shows the chosen heirloom's alone (menu.SHOWN_WHEN).
SKINS = {
    name: SpinnerOption(f"skin_{name}", OWN_SKIN, [skin["name"] for skin in HEIRLOOMS[name]["skins"]],
                        display_name="Skin", description="Your heirloom's look. Greyed when it has only one.")
    for name in OFFERED
}
glow = SliderOption(
    "glow", DEFAULT_FORCE, 1, FORCES, step=1, is_integer=True, display_name="Glow",
    description="How bright the blade glows. Greyed when the skin has no glow.",
)
mode = SpinnerOption(
    "mode", DEFAULT_MODE.capitalize(), list(MODES), display_name="Mode",
    description="Apex: all the heirloom's animations. Borderlands: ours at rest, walking and running, the game's for "
                "the rest.",
)
SIZES = {
    name: SliderOption(SAVED_SIZE.get(name, f"size_{name}"), 100, *SIZE_PERCENT, step=1, is_integer=True,
                       display_name="Heirloom Size",
                       description="The chosen heirloom's size in your hand. 100: its original size.")
    for name in OFFERED
}
draw_start = SliderOption(
    "draw_start", Timing.start, *LIMITS["start"], step=DRAW_STEP, is_integer=False, display_name="Draw Start",
    description="The higher it is, the sooner your hands show when you put your weapon away.",
)
draw_speed = SliderOption(
    "draw_speed", Timing.speed, *LIMITS["speed"], step=DRAW_STEP, is_integer=False, display_name="Draw Speed",
    description="How fast your hands draw the heirloom.",
)
# In the window's order (sketch H2): the switch leads its page, the glow follows the skin it lights.
ALL = (heirloom, model, *SKINS.values(), glow, mode, *SIZES.values(), draw_start, draw_speed)


def heirloom_of(value: Any) -> str:
    """The heirloom `value` names, the first offered for one the mod no longer offers."""
    return value if value in OFFERED else DEFAULT


def skin_of(name: str, value: Any) -> str:
    """The heirloom's skin `value` names, its own look for one it has not."""
    return value if value in SKINS[name].choices else OWN_SKIN


def glows(name: str, skin: str) -> bool:
    """Whether that skin of that heirloom has our glow: the game's skins keep their own, the force changes nothing."""
    return any(known["name"] == skin and known["glow"] is not None for known in HEIRLOOMS[name]["skins"])


def chosen_heirloom() -> str:
    return heirloom_of(model.value)


def chosen_skin(name: str | None = None) -> str:
    name = name or chosen_heirloom()
    return skin_of(name, SKINS[name].value)


def chosen_force() -> int:
    return int(round(bounded(glow)))


def chosen_mode(value: Any = None) -> str:
    """The list of the mode shown in the menu, or of `value` about to replace it; the default for an unknown one."""
    return MODES.get(mode.value if value is None else value, DEFAULT_MODE)


def fit() -> Fit:
    """The chosen heirloom's hold, at the menu's share of its own size."""
    name = chosen_heirloom()
    return Fit.of(HEIRLOOMS[name]["hold"], bounded(SIZES[name]))


def timing() -> Timing:
    return Timing(start=bounded(draw_start), speed=bounded(draw_speed))
