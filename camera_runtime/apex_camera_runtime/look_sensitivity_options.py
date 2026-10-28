"""The third-person sensitivity options (look_sensitivity.py), shown on the SENSITIVITY page.

Kevin, 2026-10-07: the game separates look and aim, mouse and controller, but not first and third person, and the
same setting does not feel the same over the shoulder. In percent of the game's own sensitivity, so 100 changes
nothing and the game's page stays the reference.

Per weapon type (Kevin, 2026-10-07 and 2026-10-08): off by default; on, each type's value replaces the aim value
while aiming with that weapon, so the number shown is the speed the player gets, whatever its optic zoom; with "BDL4"
a weapon aims in first person and keeps the game's own speed. Per optic zoom: its own switch, off by default, unfolds
one row per zoom that replaces the weapon's value, or the aim value, for that zoom. The two switches are independent
(Kevin, 2026-10-10: « ce sont deux réglages indépendants »): zoom rows once needed the per-weapon switch on.
Kevin, 2026-10-09, once 1.2.12 had shipped rows per zoom only: « si j'ai envie de régler la même sensibilité pour le
sniper, est-ce que j'ai envie d'avoir à le régler 5 fois ? ». The zoom rows came with the sniper rifle's optics and
count for every weapon since each weapon type has its optics (Kevin, 2026-10-09: « les lignes actuelles pour les
sensibilités par zoom s'appliquent pour toutes les armes »); x1 is the weapon's own aim and keeps its row.
Heavy weapons got their row with their optics: before, they always aimed in first person, and a row that changed
nothing would have read as broken (Kevin, 2026-10-08).
"""

from mods_base import BoolOption, SliderOption

from . import option_texts
from .ads_optic import ZOOMS
from .speed_fov_options import bounded

DEFAULT, MIN_PERCENT, MAX_PERCENT = 100, 25, 200
# The window draws the rows under this prefix as bars, unfolded by the switch (panel_weapon_sensitivity.py).
WEAPON_PREFIX = "sensitivity_weapon_"
WEAPONS = ("pistol", "smg", "shotgun", "assault", "sniper", "heavy")
OPTICS = tuple(f"sniper_x{zoom}" for zoom in ZOOMS)
# Under the same prefix, so it folds with the weapon rows; named for the sniper rifle, the first weapon with optics,
# so the players' saved values stay.
PER_OPTIC = WEAPON_PREFIX + "sniper_optics"
PAGE = ("sensitivity_look", "sensitivity_aim", "sensitivity_weapons", *(WEAPON_PREFIX + name for name in WEAPONS),
        PER_OPTIC, *(WEAPON_PREFIX + name for name in OPTICS))


def _percent(identifier: str, texts: dict) -> SliderOption:
    return SliderOption(identifier, DEFAULT, MIN_PERCENT, MAX_PERCENT, step=1, is_integer=True, **texts)


class LookSensitivityOptions:
    def __init__(self) -> None:
        self.look = _percent("sensitivity_look", option_texts.SENSITIVITY_LOOK)
        self.aim = _percent("sensitivity_aim", option_texts.SENSITIVITY_AIM)
        self.per_weapon = BoolOption("sensitivity_weapons", False, **option_texts.SENSITIVITY_WEAPONS)
        self.weapons = tuple(_percent(WEAPON_PREFIX + name, option_texts.SENSITIVITY_WEAPON[name])
                             for name in WEAPONS)
        self.per_optic = BoolOption(PER_OPTIC, False, **option_texts.SENSITIVITY_PER_OPTIC)
        self.optics = tuple(_percent(WEAPON_PREFIX + name, option_texts.SENSITIVITY_WEAPON[name]) for name in OPTICS)
        self.options = (self.look, self.aim, self.per_weapon, *self.weapons, self.per_optic, *self.optics)

    def values(self) -> tuple[float, float, dict]:
        """The look and aim factors, then each weapon type's while its switch is on and the optic zooms' while
        theirs is on; a hand-edited file falls back to the game's own speed."""
        look, aim = (self._factor(option) for option in (self.look, self.aim))
        rows = ()
        if self.per_weapon.value is True:
            rows = (*rows, *zip(WEAPONS, self.weapons))
        if self.per_optic.value is True:
            rows = (*rows, *zip(OPTICS, self.optics))
        return look, aim, {name: self._factor(option) for name, option in rows}

    @staticmethod
    def _factor(option: SliderOption) -> float:
        return bounded(option.value, MIN_PERCENT, MAX_PERCENT, DEFAULT) / 100
