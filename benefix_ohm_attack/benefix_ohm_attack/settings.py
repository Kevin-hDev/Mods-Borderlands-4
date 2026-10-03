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
# The lock, the catch and the bounce are the game's weapon's own, the Benefix Ohm I Got, with the lock's numbers as
# its defaults (read in the game's files on 2026-10-02, docs/attaque-rayon/enquetes/2026-10-02-accroche-du-rayon.md).
# Kevin, the same day: each with its setting in the window, the lock and the bounce with a switch, on by default.
# After his first trial, no difference to be seen between the lowest and the highest setting: "permettre au réglage
# une limite bien plus importante". The catch went from 1 m at most to 5, the lock's delay from 1 s to 3, its
# angle from 5-60 degrees to 1-90. The catch was shown as "Beam thickness": it never changed how the beam looks.
# The catch's default is Kevin's for the release, after his second trial: 200 cm (the weapon's 20 could not be felt).
width = BoundedSliderOption(
    "width", 200, 0, 500, step=10, is_integer=True,
    display_name="Catch distance",
    description="How far from your aim the beam catches an enemy, in centimetres. 0: you must aim at the enemy.",
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

lock = BoolOption(
    "lock", True,
    display_name="Target lock",
    description="The beam stays on the enemy it has touched, even when your aim strays.",
)
lock_delay = BoundedSliderOption(
    "lock_delay", 0.2, 0.0, 3.0, step=0.05, is_integer=False,
    display_name="Time before lock",
    description="Seconds the beam must stay on an enemy before it locks on.",
)
lock_angle = BoundedSliderOption(
    "lock_angle", 30, 1, 90, step=1, is_integer=True,
    display_name="Break angle",
    description="How far your aim may stray from the enemy, in degrees, before the lock lets go.",
)
bounce = BoolOption(
    "bounce", True,
    display_name="Bounce",
    description="The second enemy must stand within 20 metres of the first.",
)

# Every setting the window shows, page by page, in each page's order (menu.py): its model, Restore and Undo read
# them from here, and the SDK's own menu lists them in the same order.
BEAM_PAGE = (element, damage, width, show_bar, drain, regen, regen_delay)
LOCK_PAGE = (lock, lock_delay, lock_angle, bounce)
ALL = (*BEAM_PAGE, *LOCK_PAGE)


def element_name() -> str:
    """The element fired: the menu's, or the default one when the saved name is no longer offered."""
    name = str(element.value)
    return name if name in ELEMENTS else DEFAULT_ELEMENT


def chosen() -> tuple[str, Effect]:
    """(the game's damage type, the game's beam effect) for the element fired."""
    return ELEMENTS[element_name()]
