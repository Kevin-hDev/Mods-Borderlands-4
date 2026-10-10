"""Third-person look and aim sensitivity, mouse and controller (second list n° 4; Kevin, 2026-10-07 and 2026-10-08).

The game turns the camera in native code: no hook sees the turn (probe 1, releves/2026-10-07-sensibilite). Its own
sensitivities live in profile.sav, rewritten with each autosave, so a mod never changes them: a value written there in
third person could become the player's setting for good. The look input goes through a multiplier per key the game
keeps in memory only (look_multiplier.py); scaling the mouse's changes the turn speed (probe 3, Kevin: « nettement
plus lente sans visée et plus rapide en visant »).

In ThirdPerson and Orbit each multiplier gets the player's look or aim factor, or while aiming the held weapon type's
when the player set one; a weapon at the shoulder with a magnifying zoom takes that zoom's when the player set
one, else its own (ads_optic.py).
Anywhere else, and when the elected mod leaves, the game's own value comes back. One failure puts the game's values
back and stops the unit for the session.
"""

from typing import Any, Callable

from .ads_category import category
from .aiming import wants_to_aim
from .constants import ORBIT_MODE, THIRD_PERSON_MODE
from .generated_ads import (CATEGORY_ASSAULT, CATEGORY_HEAVY, CATEGORY_PISTOL, CATEGORY_SHOTGUN, CATEGORY_SMG,
                            CATEGORY_SNIPER)
from .look_multiplier import LookMultiplier

KEYS = ("Mouse2D", "Gamepad_Right2D")
THIRD_MODES = (THIRD_PERSON_MODE, ORBIT_MODE)
# The weapon names of look_sensitivity_options.WEAPONS.
WEAPON_NAMES = {CATEGORY_PISTOL: "pistol", CATEGORY_SMG: "smg", CATEGORY_SHOTGUN: "shotgun",
                CATEGORY_ASSAULT: "assault", CATEGORY_SNIPER: "sniper", CATEGORY_HEAVY: "heavy"}


def game_log(message: str) -> None:
    # Imported on use: the runtime is made before the game's modules can be read, as in the camera mods' tests.
    from unrealsdk import logging
    logging.info(f"[Camera Runtime] {message}")


def factor(values: tuple, mode: str, aiming: bool, weapon: str | None = None) -> float:
    # A mod built before the weapon types gives only look and aim.
    look, aim, *rest = values
    if mode not in THIRD_MODES:
        return 1.0
    if not aiming:
        return look
    weapons = rest[0] if rest else {}
    return weapons.get(weapon, aim)


def optic_weapon(weapons: dict, zoom: int, weapon: str | None) -> str | None:
    """The zoom's own row while the per-optic switch is on, else the weapon's (look_sensitivity_options.py)."""
    name = f"sniper_x{zoom}"
    return name if name in weapons else weapon


def held_weapon(actor: Any) -> str | None:
    """The held weapon's type name, or None while the animation has not caught up with a weapon change."""
    slots = actor.ActiveWeapons.Slots
    try:
        observation = category(actor, slots[0].Weapon if len(slots) else None)
    except ValueError:
        # An unreadable type keeps the aim value: the per-weapon rows are a refinement, not worth the whole unit.
        return None
    return WEAPON_NAMES.get(observation["value"]) if observation["matched"] else None


class LookSensitivity:
    def __init__(self, weak_ref: Callable, address_of: Callable, log: Callable | None = None) -> None:
        self.multipliers = tuple(LookMultiplier(key, weak_ref, address_of) for key in KEYS)
        self.log = log or game_log
        self.failed = False

    def sync(self, settings: Any, pc: Any, now_ns: int, zoom: int | None = None) -> None:
        """zoom: the optic's while a weapon aims at the shoulder with a magnifying zoom (ads_optic.held_zoom)."""
        read_values = getattr(settings, "look_sensitivity", None)
        if self.failed or not callable(read_values):
            return
        try:
            self._sync(read_values, pc, now_ns, zoom)
        except Exception as error:
            self.failed = True
            self.log(f"third-person sensitivity stopped: {type(error).__name__}")
            self.stop()

    def _sync(self, read_values: Callable, pc: Any, now_ns: int, zoom: int | None) -> None:
        located = [(multiplier, multiplier.locate(pc, now_ns)) for multiplier in self.multipliers]
        located = [(multiplier, modifier) for multiplier, modifier in located if modifier is not None]
        if not located:
            return
        wanted_factor = 1.0
        actor = getattr(pc, "OakCharacter", None)
        if actor is not None:
            mode, values = str(pc.PlayerCameraManager.GetActorCameraMode(actor)), read_values()
            aiming = wants_to_aim(actor)
            rows = aiming and mode in THIRD_MODES and len(values) > 2 and values[2]
            weapon = held_weapon(actor) if rows else None
            if rows and zoom is not None:
                weapon = optic_weapon(values[2], zoom, weapon)
            wanted_factor = factor(values, mode, aiming, weapon)
        for multiplier, modifier in located:
            multiplier.apply(modifier, wanted_factor)

    def stop(self) -> None:
        errors = []
        for multiplier in self.multipliers:
            try:
                multiplier.stop()
            except Exception as error:
                errors.append(error)
        if errors:
            raise errors[0]
