"""One presentation decision for ADS, independent of the weapon's zoom state."""

from .generated_ads import CATEGORY_PISTOL, CATEGORY_SMG, CATEGORY_SHOTGUN, CATEGORY_ASSAULT

ORDINARY_CATEGORIES = frozenset((CATEGORY_PISTOL, CATEGORY_SMG, CATEGORY_SHOTGUN, CATEGORY_ASSAULT))


def decide(*, aiming: bool, enabled: bool, category: int | None,
           foot_mode: str, vehicle: bool, pending: bool, supported: bool) -> str:
    if type(aiming) is not bool:
        return "native"
    if not aiming:
        return "hip"
    flags = (enabled, vehicle, pending, supported)
    if (any(type(flag) is not bool for flag in flags) or not enabled or vehicle
            or pending or not supported or type(foot_mode) is not str
            or foot_mode != "ThirdPerson" or type(category) is not int
            or category not in ORDINARY_CATEGORIES):
        return "native"
    return "third"
