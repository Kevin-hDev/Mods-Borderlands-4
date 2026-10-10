"""One presentation decision for ADS, independent of the weapon's zoom state."""

from .ads_optic import CHOICES


def decide(*, aiming: bool, enabled: bool, category: int | None,
           foot_mode: str, vehicle: bool, pending: bool, supported: bool, optic: bool = False) -> str:
    """optic: the weapon type's row has a shoulder zoom ticked and the .dll can show it (ads_optic.py); without, the
    weapon keeps the game's own aim in first person, the "BDL4" choice (Kevin, 2026-10-09)."""
    if type(aiming) is not bool:
        return "native"
    if not aiming:
        return "hip"
    flags = (enabled, vehicle, pending, supported)
    if (any(type(flag) is not bool for flag in flags) or not enabled or vehicle
            or pending or not supported or type(foot_mode) is not str
            or foot_mode != "ThirdPerson" or type(category) is not int
            or category not in CHOICES or optic is not True):
        return "native"
    return "third"
