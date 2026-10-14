"""The vehicle guns' damage formula: the one value a personal vehicle's shots follow (spec section 3.5).

Measured on 2026-10-14 (docs/investigations/vehicle_driving/degats/): a machine gun bullet deals exactly the attribute
calc_vehicle_weapon_damage_SMG resolved for the driver, a rocket the RPG one, and both take calc_vehicle_weapon_damage
as their level. That attribute's definition is a balance formula whose Scalar is a constant, 1.0: written five times
over, the bullets dealt five times as much, and written back they dealt the game's damage again. The FireProjectile
behaviors' damage, which the mod wrote up to 1.0.8, changed nothing.

The game holds one definition for every personal vehicle, and hands it resolved only in the answer of
AddModifierToGbxAttribute, which takes the attribute by reference: asked with a modifier of 0, removed at once (three
times without harm on 2026-10-14). The pointer is built with the parameter's own definition type: one built so, passed
to a parameter with no type, crashed the game (2026-09-28). A refusal is said once, and the game not asked again.
"""

from typing import Any

import unrealsdk
from unrealsdk.unreal import FGbxDefPtr

from . import report

LIBRARY = "/Script/GbxEngine.GbxAttributeBlueprintLibrary"
ADDER = "AddModifierToGbxAttribute"
REMOVER = "RemoveAttributeModifier"
ATTRIBUTE = "calc_vehicle_weapon_damage"
KINDS = "EGbxAttributeModifierType"
OUTCOMES = "EGbxAttributeModifierActionExecOutput"

# The Scalar the game gave at the first reading of this game: the definition outlives every vehicle, and a raise left
# behind would otherwise be taken for the game's own at the next vehicle and multiplied again.
_game: float | None = None
_refused = False


class Scalar:
    """The formula's Scalar where the game reads it: the fields are walked at each use, never kept."""

    def __init__(self, definition: Any) -> None:
        self._definition = definition

    @property
    def constant(self) -> float:
        return float(self._definition.Value.Scalar.constant)

    @constant.setter
    def constant(self, value: float) -> None:
        self._definition.Value.Scalar.constant = value


def game_value() -> float | None:
    return _game


def find(driver: Any) -> Scalar | None:
    """The formula's Scalar, asked of the game with the driver as context; None without a driver or once refused."""
    global _game, _refused
    if driver is None or _refused:
        return None
    try:
        definition = _resolve(driver)
    except Exception as exc:
        definition = None
        report.error_once("formula:error", f"{ATTRIBUTE} could not be asked of the game, weapon damage left to the "
                                           f"game: {exc!r}")
    if definition is None:
        _refused = True
        return None
    scalar = Scalar(definition)
    if _game is None:
        _game = scalar.constant
    return scalar


def _resolve(driver: Any) -> Any:
    cls = unrealsdk.find_class(LIBRARY)
    kind = getattr(cls._find(ADDER)._find("attribute"), "Struct", None)
    if kind is None:
        report.error_once("formula:untyped", f"{ADDER}'s attribute has no definition type, never called: weapon "
                                             f"damage left to the game")
        return None
    library = cls.ClassDefaultObject
    outcome = next(iter(unrealsdk.find_enum(OUTCOMES)))
    answer = library.AddModifierToGbxAttribute(FGbxDefPtr(ATTRIBUTE, kind), driver, unrealsdk.find_enum(KINDS).PostAdd,
                                               0.0, True, outcome)
    library.RemoveAttributeModifier(answer[0])
    # In game the attribute came back second, resolved; one never resolved has no address.
    for item in answer[1:]:
        if isinstance(item, FGbxDefPtr) and item._get_address() != 0:
            return item
    report.error_once("formula:unresolved", f"the game gave {ATTRIBUTE} back unresolved: weapon damage left to the game")
    return None
