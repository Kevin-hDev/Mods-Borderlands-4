"""One camera profile as the profiles' file keeps it (profile_store.py): its name, its keys and its five values,
checked at the door, and its row in the file. A refusal names the menu's line for it (panel_profile_text.py)."""

import re
from dataclasses import asdict, dataclass

from . import profile_values
from .key_option import normalize_controller_key, normalize_keyboard_key

# 24 characters fit a row's label on the PROFILS page (decisions of 2026-10-12).
MAX_NAME, MAX_ID = 24, 10_000
# Letters with their accents, digits, spaces, hyphens, apostrophes and underscores.
_NAME = re.compile(r"[\w '’-]+")


class Refused(ValueError):
    """A change the store does not take; reason names the menu's line for it."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Profile:
    ident: int
    name: str
    values: profile_values.Values
    keyboard: str | None = None
    controller: str | None = None


def checked_name(name) -> str:
    if type(name) is not str:
        raise Refused("name_invalid")
    name = name.strip()
    if not 1 <= len(name) <= MAX_NAME or not _NAME.fullmatch(name) or not any(char.isalnum() for char in name):
        raise Refused("name_invalid")
    return name


def normalized_keys(keyboard, controller) -> tuple:
    try:
        return normalize_keyboard_key(keyboard), normalize_controller_key(controller)
    except ValueError:
        raise Refused("key_invalid") from None


def _shares_key(keys: tuple, other: Profile) -> bool:
    return any(mine is not None and mine == theirs for mine, theirs in zip(keys, (other.keyboard, other.controller)))


def clash(others, profile: Profile) -> None:
    for other in others:
        if other.ident == profile.ident:
            raise Refused("id_taken")
        if other.name.casefold() == profile.name.casefold():
            raise Refused("name_taken")
        if _shares_key((profile.keyboard, profile.controller), other):
            raise Refused("key_taken")


def checked_keys(keyboard, controller, others, ident: int | None) -> tuple:
    """The two keys as profile ident would keep them, or Refused: the profile window refuses a key as it is chosen,
    rather than at SAVE."""
    keys = normalized_keys(keyboard, controller)
    if any(other.ident != ident and _shares_key(keys, other) for other in others):
        raise Refused("key_taken")
    return keys


def read(entry) -> Profile:
    if type(entry) is not dict:
        raise ValueError("invalid profile entry")
    ident = entry.get("id")
    if type(ident) is not int or not 1 <= ident <= MAX_ID:
        raise ValueError("invalid profile identifier")
    values = profile_values.make(**{field: entry.get(field) for field in profile_values.FIELDS})
    keys = normalized_keys(entry.get("keyboard"), entry.get("controller"))
    return Profile(ident, checked_name(entry.get("name")), values, *keys)


def written(profile: Profile) -> dict:
    return {"id": profile.ident, "name": profile.name, **asdict(profile.values),
            "keyboard": profile.keyboard, "controller": profile.controller}
