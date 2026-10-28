"""The optics ticked on the AIMING page: one row of boxes per weapon type, "BDL4" then its zooms (Kevin, 2026-10-09;
the sniper rifle's row first, every weapon type's in the evening).

One saved number per row with one bit per zoom of that row: 0 is "BDL4", the game's own aim in first person, so
"BDL4" and a zoom can never be ticked together; ticking a zoom unticks "BDL4", unticking the last zoom ticks it again.
Hidden from the SDK's text menu, where a number would mean nothing; the window draws the rows.
"""

from typing import NamedTuple

from mods_base import SliderOption

from . import option_texts
from .ads_optic import CHOICES, X1
from .generated_ads import (CATEGORY_ASSAULT, CATEGORY_HEAVY, CATEGORY_PISTOL, CATEGORY_SHOTGUN, CATEGORY_SMG,
                            CATEGORY_SNIPER)

KEYBOARD_ID, CONTROLLER_ID = "sniper_zoom_key", "sniper_zoom_controller"


class Row(NamedTuple):
    identifier: str
    category: int
    default: tuple  # the zooms ticked on a new install


# The game's weapon order, as on the SENSITIVITY page. x1 ticked by default: those weapons aimed at the shoulder before
# their rows; heavy weapons kept the game's aim, and sniper rifles' row starts on "BDL4" since it came (Kevin: « ok
# pour ça », docs/third_person_fov/camera/2026-10-09-plan-optiques-toutes-armes.md).
ROWS = (Row("pistol_optics", CATEGORY_PISTOL, (X1,)), Row("smg_optics", CATEGORY_SMG, (X1,)),
        Row("shotgun_optics", CATEGORY_SHOTGUN, (X1,)), Row("assault_optics", CATEGORY_ASSAULT, (X1,)),
        Row("sniper_optics", CATEGORY_SNIPER, ()), Row("heavy_optics", CATEGORY_HEAVY, ()))
IDENTIFIERS = tuple(row.identifier for row in ROWS)
CHOICES_OF = {row.identifier: CHOICES[row.category] for row in ROWS}


def mask_of(zooms: tuple, choices: tuple) -> int:
    return sum(1 << choices.index(zoom) for zoom in zooms)


def ticked(mask, choices: tuple) -> tuple:
    """The ticked zooms, smallest first; a hand-edited value reads as "BDL4"."""
    if isinstance(mask, float) and mask.is_integer():
        mask = int(mask)
    if type(mask) is not int or not 0 <= mask < 1 << len(choices):
        return ()
    return tuple(zoom for bit, zoom in enumerate(choices) if mask & (1 << bit))


def toggled(mask, zoom: int | None, choices: tuple) -> int:
    """The number after a click on a box: None is the "BDL4" box, which unticks every zoom."""
    if zoom is None:
        return 0
    return mask_of(ticked(mask, choices), choices) ^ (1 << choices.index(zoom))


class WeaponOpticOptions:
    def __init__(self, commands) -> None:
        self.commands = commands
        self.options = tuple(
            SliderOption(row.identifier, mask_of(row.default, CHOICES[row.category]), 0,
                         (1 << len(CHOICES[row.category])) - 1, step=1, is_integer=True, is_hidden=True,
                         **option_texts.WEAPON_OPTICS[row.identifier])
            for row in ROWS)
        self._by_category = {row.category: (option, CHOICES[row.category]) for row, option in zip(ROWS, self.options)}

    def weapon_ticked(self, category) -> tuple:
        """The ticked zooms of that weapon type's row; a type without a row is "BDL4"."""
        option, choices = self._by_category.get(category, (None, ()))
        return ticked(option.value, choices) if option is not None else ()

    def sniper_ticked(self) -> tuple:
        """The sniper rifle's row, as runtimes built before the other rows read it."""
        return self.weapon_ticked(CATEGORY_SNIPER)

    def keys(self) -> tuple:
        """The zoom key on the keyboard and on the controller, set on the COMMANDS page."""
        return tuple(self.commands.option(identifier).value for identifier in (KEYBOARD_ID, CONTROLLER_ID))
