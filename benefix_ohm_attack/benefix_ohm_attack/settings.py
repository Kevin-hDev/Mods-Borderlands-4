"""The beam attack's settings and the game names each element stands for.

An element is two things of the game: its damage type (damagetype'...' in the game's data) and one of its beam
effects. Fire is the default (Kevin, 2026-10-01).
"""

from mods_base import BoolOption, SpinnerOption

from .beam import Effect
from .slider_option import BoundedSliderOption

WEAPON_BEAMS = "/Game/Gear/Weapons/_Shared/Effects/Systems/GenericLaser/"


def _effect(folder: str, name: str, **driven: object) -> Effect:
    return Effect(f"{folder}{name}.{name}", **driven)


# Menu name: (the game's damage type, the game's beam effect). The menu's names are letters only: the energy bar
# is told them, and takes nothing else (energy_service.py).
ELEMENTS = {
    "Fire": ("Fire", _effect(WEAPON_BEAMS, "NS_Beam_Energy_Incendiary")),
    "Shock": ("Shock", _effect(WEAPON_BEAMS, "NS_Beam_Energy_Shock")),
    "Corrosive": ("Corrosive", _effect(WEAPON_BEAMS, "NS_Beam_Energy_Corrosive")),
    "Cryo": ("Cryo", _effect(WEAPON_BEAMS, "NS_Beam_Energy_Cryo")),
    "Radiation": ("Radiation", _effect(WEAPON_BEAMS, "NS_Beam_Energy_Radiation")),
    # No element: the lightning of the weapon the mod is named after, the Benefix Ohm I Got, white as Kevin asked
    # (2026-10-01, seen in game: "un éclair, il me va"). The five beams above have no colour to set, and the one
    # other beam tried, NS_Laser_Basic_Pulse, drew nothing in game (docs/attaque-rayon/enquetes/
    # 2026-10-01-rayon-blanc.md).
    "Kinetic": ("Normal", _effect(WEAPON_BEAMS, "NS_BOR_OhmIGot_Beam_Energy_Lightning", position=True)),
}
DEFAULT_ELEMENT = "Fire"
# How many times a second the beam hits what it is on. The game's own beam gun hits 8.7 times a second.
HITS_PER_SECOND = 5.0
# How far the camera's ray looks for a target, in centimetres. Kevin, 2026-10-01: the beam has no range limit of its
# own (the 50 m setting stopped it short of far enemies). A ray needs an end all the same: this one is a kilometre
# away.
REACH = 100000.0

element = SpinnerOption(
    "element", DEFAULT_ELEMENT, list(ELEMENTS), wrap_enabled=True,
    display_name="Element",
    description="What the beam is made of.",
)
damage = BoundedSliderOption(
    "damage", 75, 5, 2000, step=5, is_integer=True,
    display_name="Damage per second",
    description="The damage at level 1. The beam grows with your level from this value.",
)
show_bar = BoolOption(
    "show_bar", True,
    display_name="Energy bar",
    description="Shows the energy bar under your stamina bar while the beam is in use.",
)
drain = BoundedSliderOption(
    "drain", 20, 0, 100, step=1, is_integer=True,
    display_name="Energy per second",
    description="What the beam spends. 0: the energy never runs out.",
)
regen = BoundedSliderOption(
    "regen", 25, 1, 100, step=1, is_integer=True,
    display_name="Recharge per second",
    description="How fast the energy comes back.",
)
regen_delay = BoundedSliderOption(
    "regen_delay", 2.0, 0.0, 10.0, step=0.5, is_integer=False,
    display_name="Delay before recharge",
    description="Seconds without firing before the energy comes back.",
)

# Every setting the window shows, in its page's order (menu.py): its model, Restore and Undo read them from here, and
# the SDK's own menu lists them in the same order.
ALL = (element, damage, show_bar, drain, regen, regen_delay)


def element_name() -> str:
    """The element fired: the menu's, or the default one when the saved name is no longer offered."""
    name = str(element.value)
    return name if name in ELEMENTS else DEFAULT_ELEMENT


def chosen() -> tuple[str, Effect]:
    """(the game's damage type, the game's beam effect) for the element fired."""
    return ELEMENTS[element_name()]
