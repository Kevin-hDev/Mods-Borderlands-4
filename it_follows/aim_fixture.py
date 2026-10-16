"""Fake weapons for the aim's tests (normal/aim.py): an enemy's ActiveWeapons with fire behaviours, each with the
three fields as GbxAttributeFloat, as trials 50 and 51 read them; a struct read as a copy as well as by reference."""

import types
from typing import Any

FIELDS = ("aiaccuracy", "aiminaccuracy", "aiprojectilespeed")


class Attribute:
    def __init__(self, value: float) -> None:
        self.Value, self.BaseValue = value, value


class Named:
    def __init__(self, name: str) -> None:
        self.Name = name


class Behaviour:
    """A fire behaviour; copying, a field read gives a copy, written back only by setattr."""

    def __init__(self, path: str, accuracy: float = 7.5, least: float = 0.25, speed: float = 0.45,
                 copying: bool = False) -> None:
        self.Class = types.SimpleNamespace(_superfields=lambda: [Named("WeaponBehavior_FireProjectile"),
                                                                 Named("WeaponBehavior_Use")])
        self.path, self.copying, self.freed = path, copying, False
        self.stored = dict(zip(FIELDS, (Attribute(accuracy), Attribute(least), Attribute(speed))))

    def __getattr__(self, name: str) -> Any:
        stored = self.__dict__["stored"].get(name)
        if stored is None:
            raise AttributeError(name)
        if not self.__dict__["copying"]:
            return stored
        copy = Attribute(0.0)
        copy.Value, copy.BaseValue = stored.Value, stored.BaseValue
        return copy

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__dict__.get("stored", {}):
            self.stored[name] = Attribute(0.0)
            self.stored[name].Value, self.stored[name].BaseValue = value.Value, value.BaseValue
            return
        object.__setattr__(self, name, value)

    def _path_name(self) -> str:
        return self.path

    def values(self) -> dict:
        return {name: [round(attribute.Value, 4), round(attribute.BaseValue, 4)]
                for name, attribute in self.stored.items()}


class Sway:
    """A behaviour of the weapon that is no fire behaviour."""
    Class = types.SimpleNamespace(_superfields=lambda: [Named("WeaponBehavior_Sway"), Named("WeaponBehavior")])


def weapons(*held: list | None) -> types.SimpleNamespace:
    """ActiveWeapons: one slot per list of behaviours, None an empty slot."""
    slots = [types.SimpleNamespace(Weapon=None if behaviours is None
                                   else types.SimpleNamespace(behaviors=[Sway(), *behaviours]))
             for behaviours in held]
    return types.SimpleNamespace(Slots=slots)
