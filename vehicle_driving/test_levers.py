"""Tests the levers: what each setting multiplies on Kevin's vehicle, and a vehicle built otherwise."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


sdk_stubs.install()

from vehicle_driving import levers  # noqa: E402

ATTRIBUTES = ("maxspeed", "BoostMaxSpeed", "MaxAccel", "BoostMaxAccel")

car = sdk_stubs.Vehicle()
found, missing = levers.targets(car)
keys = [target.key for target in found]
check("the springs of driving and boost, every spring of each set",
      keys[:6] == [f"YawSpring_Hovering[{i}]" for i in range(3)] + [f"YawSpring_Boosting[{i}]" for i in range(3)])
check("the four attributes of the driver, base before value",
      keys[6:14] == [f"{name}.{field}" for name in ATTRIBUTES for field in ("BaseValue", "Value")])
check("the jump height closes the list", keys[14:] == ["PowerslideJumpHeight"])
check("nothing is missing on Kevin's vehicle", missing == [])
by_key = {target.key: target for target in found}
check("each lever follows its setting",
      by_key["YawSpring_Boosting[1]"].setting == "turn_speed" and by_key["BoostMaxSpeed.Value"].setting == "max_speed"
      and by_key["MaxAccel.BaseValue"].setting == "acceleration"
      and by_key["PowerslideJumpHeight"].setting == "jump_height")
check("an attribute's value names its base, and nothing else names one",
      by_key["MaxAccel.Value"].base_key == "MaxAccel.BaseValue" and by_key["MaxAccel.BaseValue"].base_key is None
      and by_key["PowerslideJumpHeight"].base_key is None and by_key["YawSpring_Hovering[0]"].base_key is None)
check("springs and jump belong to the vehicle, attributes to the driver",
      by_key["YawSpring_Hovering[0]"].owner == levers.VEHICLE and by_key["PowerslideJumpHeight"].owner == levers.VEHICLE
      and by_key["maxspeed.Value"].owner == levers.DRIVER)
spring = by_key["YawSpring_Hovering[1]"]
check("a lever points at the live value", getattr(spring.holder, spring.field) == 3.5)
check("the idle spring and the braking are left alone", not any("Idle" in key or "Braking" in key for key in keys))

other = sdk_stubs.Vehicle("OakVehicle_2")
del other.OakVehicleMovement.HoverSetup.YawSpring_Boosting
other.DriverPawn = None
found, missing = levers.targets(other)
check("a vehicle built otherwise gives what it has and names what it lacks",
      missing == ["YawSpring_Boosting", *ATTRIBUTES]
      and [target.key for target in found] == [f"YawSpring_Hovering[{i}]" for i in range(3)] + ["PowerslideJumpHeight"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
