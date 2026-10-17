"""Which game values each setting multiplies, and where they sit on a vehicle (spec sections 2 and 3.5).

Sessions 2 to 9 of the driving investigation (2026-09-18), verified in game: the yaw
springs of driving and boost turn the vehicle quicker, the jump height holds, and the driver's speed and acceleration
attributes hold, base and value, the game refilling the vehicle's own copies from them every frame. The idle spring
and the braking were left alone in every session and stay so.
Sessions 11 and 12 (2026-10-03), verified in game: the driver's reverse speed and boost consumption and the vehicle's
damage taken hold when written, and each changes the game. Measured on 2026-10-14: the guns follow their damage
formula (damage_formula.py), not the FireProjectile behaviors' damage the mod wrote up to 1.0.8.
"""

from dataclasses import dataclass
from typing import Any

from . import damage_formula

VEHICLE = "vehicle"
DRIVER = "driver"
# The guns' damage formula is the game's own, one for every vehicle: nothing the game destroys carries it.
GAME = "game"
SPRINGS = ("YawSpring_Hovering", "YawSpring_Boosting")
ATTRIBUTES = (("max_speed", "maxspeed"), ("max_speed", "BoostMaxSpeed"),
              ("acceleration", "MaxAccel"), ("acceleration", "BoostMaxAccel"),
              ("reverse_speed", "ReverseSpeed"), ("boost_cost", "BoostConsumptionRateScalar"))
DRIVER_NAMES = {name for _, name in ATTRIBUTES}
JUMP = "PowerslideJumpHeight"
DAMAGE_TAKEN = "DamageTakenMultiplier"


@dataclass(frozen=True)
class Target:
    """One game value: `holder.field` is the live value, written in place; `setting` names its factor in
    settings.factors(); `owner` names the game object that carries it, `source`: the vehicle or its driver, each held
    by its own weak pointer, or None for the game itself, which outlives them (spec section 3.5)."""

    key: str
    setting: str
    owner: str
    source: Any
    holder: Any
    field: str
    # An attribute's Value names its BaseValue: the game computes a value from its base (spec section 3.2).
    base_key: str | None = None
    # The game's own value when it is known for the whole game: written from it, never from what is found, a value is
    # never multiplied twice even if a put back never came.
    game: float | None = None


def targets(vehicle: Any, with_game: bool = True, with_driver: bool = True) -> tuple[list[Target], list[str]]:
    """Every lever this vehicle has, and the name of each one it lacks: only Kevin's vehicles were measured, and another
    model may be built otherwise (spec section 3.4). Without `with_game`, the guns' damage formula, one for every
    vehicle, is left out: a co-op guest's vehicle never writes it (guests.py). Without `with_driver`, the driver's
    attributes are: on a co-op guest's game they come from the host's (seat.on_guest_game)."""
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
    for setting, name in ATTRIBUTES if with_driver else ():
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
    if not with_game:
        return found, missing
    scalar = damage_formula.find(driver)
    if scalar is None:
        missing.append(damage_formula.ATTRIBUTE)
    else:
        found.append(Target(f"{damage_formula.ATTRIBUTE}.Scalar", "weapon_damage", GAME, None, scalar, "constant",
                            game=damage_formula.game_value()))
    return found, missing


def comes_late(name: str) -> bool:
    """Whether a lever missing when the vehicle is taken may still come, and is looked for again: the driver may sit
    down after the vehicle became the pawn (the order was never measured), and the guns' damage formula is asked with
    the driver as context."""
    return name in DRIVER_NAMES or name == damage_formula.ATTRIBUTE


def _pair(found: list[Target], key: str, setting: str, owner: str, source: Any, pair: Any) -> None:
    # The base first: the value's check reads whether the game changed the base in the same pass.
    found.append(Target(f"{key}.BaseValue", setting, owner, source, pair, "BaseValue"))
    found.append(Target(f"{key}.Value", setting, owner, source, pair, "Value", base_key=f"{key}.BaseValue"))
