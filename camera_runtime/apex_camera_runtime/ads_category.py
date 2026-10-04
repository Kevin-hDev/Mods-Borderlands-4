"""Read the native animation category only when its weapon is still held."""

import enum

from .generated_ads import CATEGORY_MAX, MIN_POINTER, MAX_TEXT


def address(item) -> int:
    if item is None:
        return 0
    value = item._get_address()
    if type(value) is not int or not MIN_POINTER <= value < 2**64 or value % 8:
        raise ValueError("invalid ADS reference")
    return value


def category(actor, weapon) -> dict:
    animation = actor.Mesh.GetAnimInstance()
    if animation is None or weapon is None:
        return {"matched": False}
    if address(animation.CurrentWeapon) != address(weapon):
        return {"matched": False}
    value = animation.WeaponType
    if (not isinstance(value, enum.Enum) or not value.name
            or not 0 <= int(value) <= CATEGORY_MAX):
        raise ValueError("category enum unavailable")
    return {"matched": True, "value": int(value), "name": value.name[:MAX_TEXT]}
