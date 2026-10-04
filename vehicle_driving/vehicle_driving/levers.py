"""Which game values each setting multiplies, and where they sit on a vehicle (spec sections 2 and 3.5).

Sessions 2 to 9 of the driving investigation (2026-09-18), verified in game: the yaw
springs of driving and boost turn the vehicle quicker, the jump height holds, and the driver's speed and acceleration
attributes hold, base and value, the game refilling the vehicle's own copies from them every frame. The idle spring
and the braking were left alone in every session and stay so.
Sessions 11 and 12 (2026-10-03), verified in game: the driver's reverse speed and boost consumption, the vehicle's
damage taken and each weapon's damage per shot hold when written, and each changes the game.
"""

from dataclasses import dataclass
from typing import Any

VEHICLE = "vehicle"
DRIVER = "driver"
SPRINGS = ("YawSpring_Hovering", "YawSpring_Boosting")
ATTRIBUTES = (("max_speed", "maxspeed"), ("max_speed", "BoostMaxSpeed"),
              ("acceleration", "MaxAccel"), ("acceleration", "BoostMaxAccel"),
              ("reverse_speed", "ReverseSpeed"), ("boost_cost", "BoostConsumptionRateScalar"))
DRIVER_NAMES = {name for _, name in ATTRIBUTES}
JUMP = "PowerslideJumpHeight"
DAMAGE_TAKEN = "DamageTakenMultiplier"
WEAPONS = "VehicleWeapons"
WEAPON = "weapon"
FIRING = "FireProjectile"
# Four weapons of four behaviors each on Kevin's vehicle (session 11): a model built otherwise must not make the search
# run long.
MAX_WEAPONS = 8
MAX_BEHAVIORS = 8


@dataclass(frozen=True)
class Target:
    """One game value: `holder.field` is the live value, written in place; `setting` names its factor in
    settings.factors(); `owner` names the game object that carries it, `source`: the vehicle, its driver, or one
    weapon's firing behavior, each held by its own weak pointer (spec section 3.5)."""

    key: str
    setting: str
    owner: str
    source: Any
    holder: Any
    field: str
    # An attribute's Value names its BaseValue: the game computes a value from its base (spec section 3.2).
    base_key: str | None = None


def targets(vehicle: Any) -> tuple[list[Target], list[str]]:
    """Every lever this vehicle has, and the name of each one it lacks: only Kevin's vehicles were measured, and another
    model may be built otherwise (spec section 3.4)."""
    found: list[Target] = []
    missing: list[str] = []
    hover = vehicle.OakVehicleMovement.HoverSetup
    for name in SPRINGS:
        spring_set = getattr(hover, name, None)
        if spring_set is None:
            missing.append(name)
            continue
        found += [Target(f"{name}[{index}]", "turn_speed", VEHICLE, vehicle, spring, "Stiffness")
                  for index, spring in enumerate(spring_set.Springs)]
    driver = getattr(vehicle, "DriverPawn", None)
    component = getattr(driver, "VehicleDriverComponent", None)
    attributes = getattr(component, "VehicleAttributesState", None)
    for setting, name in ATTRIBUTES:
        pair = getattr(attributes, name, None)
        if pair is None:
            missing.append(name)
            continue
        _pair(found, name, setting, DRIVER, driver, pair)
    jump = getattr(hover, JUMP, None)
    if jump is None:
        missing.append(JUMP)
    else:
        found.append(Target(JUMP, "jump_height", VEHICLE, vehicle, jump, "constant"))
    taken = getattr(getattr(vehicle, "DamageState", None), DAMAGE_TAKEN, None)
    if taken is None:
        missing.append(DAMAGE_TAKEN)
    else:
        _pair(found, DAMAGE_TAKEN, "damage_taken", VEHICLE, vehicle, taken)
    _weapons(vehicle, found, missing)
    return found, missing


def comes_late(name: str) -> bool:
    """Whether a lever missing when the vehicle is taken may still come, and is looked for again: the driver may sit
    down after the vehicle became the pawn (the order was never measured), and the vehicle first summoned after loading
    had its weapons without their damage, which the next vehicle had (session 13, 2026-10-04)."""
    return name in DRIVER_NAMES or name == WEAPONS or name.startswith(f"{WEAPON}[")


def _pair(found: list[Target], key: str, setting: str, owner: str, source: Any, pair: Any) -> None:
    # The base first: the value's check reads whether the game changed the base in the same pass.
    found.append(Target(f"{key}.BaseValue", setting, owner, source, pair, "BaseValue"))
    found.append(Target(f"{key}.Value", setting, owner, source, pair, "Value", base_key=f"{key}.BaseValue"))


def _weapons(vehicle: Any, found: list[Target], missing: list[str]) -> None:
    """Each weapon's damage per shot, on its firing behavior. Every weapon is written, active or not: switching weapons
    at the wheel needs nothing more."""
    weapons = getattr(vehicle, WEAPONS, None)
    count = min(len(weapons), MAX_WEAPONS) if weapons is not None else 0
    if count == 0:
        missing.append(WEAPONS)
        return
    for index in range(count):
        owner = f"{WEAPON}[{index}]"
        behavior = _firing(weapons[index])
        damage = getattr(behavior, "damage", None)
        if damage is None:
            missing.append(f"{owner}.damage")
            continue
        _pair(found, f"{owner}.damage", "weapon_damage", owner, behavior, damage)


def _firing(weapon: Any) -> Any:
    """The firing behavior, by its type: it was the first of four in session 11, but nothing says it stays first."""
    behaviors = getattr(weapon, "behaviors", None)
    if behaviors is None:
        return None
    for index in range(min(len(behaviors), MAX_BEHAVIORS)):
        behavior = behaviors[index]
        if FIRING in str(getattr(getattr(behavior, "Class", None), "Name", "")):
            return behavior
    return None
