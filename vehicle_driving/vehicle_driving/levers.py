"""Which game values each setting multiplies, and where they sit on a vehicle (spec section 2).

Sessions 2 to 9 of the driving investigation (2026-09-18), verified in game: the yaw
springs of driving and boost turn the vehicle quicker, the jump height holds, and the driver's speed and acceleration
attributes hold, base and value, the game refilling the vehicle's own copies from them every frame. The idle spring
and the braking were left alone in every session and stay so.
"""

from dataclasses import dataclass
from typing import Any

VEHICLE = "vehicle"
DRIVER = "driver"
SPRINGS = ("YawSpring_Hovering", "YawSpring_Boosting")
ATTRIBUTES = (("max_speed", "maxspeed"), ("max_speed", "BoostMaxSpeed"),
              ("acceleration", "MaxAccel"), ("acceleration", "BoostMaxAccel"))
JUMP = "PowerslideJumpHeight"


@dataclass(frozen=True)
class Target:
    """One game value: `holder.field` is the live value, written in place; `setting` names its factor in
    settings.factors(); `owner` says whether it lives on the vehicle or on its driver."""

    key: str
    setting: str
    owner: str
    holder: Any
    field: str
    # An attribute's Value names its BaseValue: the game computes a value from its base (spec section 3.2).
    base_key: str | None = None


def targets(vehicle: Any) -> tuple[list[Target], list[str]]:
    """Every lever this vehicle has, and the name of each one it lacks: only Kevin's vehicle was measured, and another
    model may be built otherwise (spec section 3.4)."""
    found: list[Target] = []
    missing: list[str] = []
    hover = vehicle.OakVehicleMovement.HoverSetup
    for name in SPRINGS:
        spring_set = getattr(hover, name, None)
        if spring_set is None:
            missing.append(name)
            continue
        found += [Target(f"{name}[{index}]", "turn_speed", VEHICLE, spring, "Stiffness")
                  for index, spring in enumerate(spring_set.Springs)]
    driver = getattr(vehicle, "DriverPawn", None)
    component = getattr(driver, "VehicleDriverComponent", None)
    attributes = getattr(component, "VehicleAttributesState", None)
    for setting, name in ATTRIBUTES:
        pair = getattr(attributes, name, None)
        if pair is None:
            missing.append(name)
            continue
        # The base first: the value's check reads whether the game changed the base in the same pass.
        found.append(Target(f"{name}.BaseValue", setting, DRIVER, pair, "BaseValue"))
        found.append(Target(f"{name}.Value", setting, DRIVER, pair, "Value", base_key=f"{name}.BaseValue"))
    jump = getattr(hover, JUMP, None)
    if jump is None:
        missing.append(JUMP)
    else:
        found.append(Target(JUMP, "jump_height", VEHICLE, jump, "constant"))
    return found, missing
