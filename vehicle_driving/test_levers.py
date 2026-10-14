"""Tests the levers: what each setting multiplies on Kevin's vehicle, the guns' damage formula, and a vehicle built
otherwise."""

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

ATTRIBUTES = ("maxspeed", "BoostMaxSpeed", "MaxAccel", "BoostMaxAccel", "ReverseSpeed", "BoostConsumptionRateScalar")
PAIR = ("BaseValue", "Value")

car = sdk_stubs.Vehicle()
found, missing = levers.targets(car)
keys = [target.key for target in found]
check("the springs of driving and boost, every spring of each set",
      keys[:6] == [f"YawSpring_Hovering[{i}]" for i in range(3)] + [f"YawSpring_Boosting[{i}]" for i in range(3)])
check("the six attributes of the driver, base before value",
      keys[6:18] == [f"{name}.{field}" for name in ATTRIBUTES for field in PAIR])
check("then the jump, the damage the vehicle takes and the Scalar of the guns' damage formula",
      keys[18:] == ["PowerslideJumpHeight", "DamageTakenMultiplier.BaseValue", "DamageTakenMultiplier.Value",
                    "calc_vehicle_weapon_damage.Scalar"])
check("nothing is missing on Kevin's vehicle", missing == [])
by_key = {target.key: target for target in found}
check("each lever follows its setting",
      by_key["YawSpring_Boosting[1]"].setting == "turn_speed" and by_key["BoostMaxSpeed.Value"].setting == "max_speed"
      and by_key["MaxAccel.BaseValue"].setting == "acceleration"
      and by_key["PowerslideJumpHeight"].setting == "jump_height"
      and by_key["ReverseSpeed.Value"].setting == "reverse_speed"
      and by_key["BoostConsumptionRateScalar.BaseValue"].setting == "boost_cost"
      and by_key["DamageTakenMultiplier.Value"].setting == "damage_taken"
      and by_key["calc_vehicle_weapon_damage.Scalar"].setting == "weapon_damage")
check("a value names its base, and nothing else names one",
      by_key["MaxAccel.Value"].base_key == "MaxAccel.BaseValue" and by_key["MaxAccel.BaseValue"].base_key is None
      and by_key["PowerslideJumpHeight"].base_key is None and by_key["YawSpring_Hovering[0]"].base_key is None)
check("each value names the game object that carries it: the vehicle, its driver, or the game itself",
      by_key["YawSpring_Hovering[0]"].owner == levers.VEHICLE and by_key["YawSpring_Hovering[0]"].source is car
      and by_key["maxspeed.Value"].owner == levers.DRIVER and by_key["maxspeed.Value"].source is car.DriverPawn
      and by_key["DamageTakenMultiplier.Value"].owner == levers.VEHICLE
      and by_key["DamageTakenMultiplier.Value"].source is car
      and by_key["calc_vehicle_weapon_damage.Scalar"].owner == levers.GAME
      and by_key["calc_vehicle_weapon_damage.Scalar"].source is None)
formula = by_key["calc_vehicle_weapon_damage.Scalar"]
check("the formula's Scalar is read where the game reads it, and its game value known for the whole game",
      getattr(formula.holder, formula.field) == 1.0 and formula.game == 1.0
      and all(target.game is None for target in found if target is not formula))
spring = by_key["YawSpring_Hovering[1]"]
check("a lever points at the live value", getattr(spring.holder, spring.field) == 3.5)
check("the idle spring and the braking are left alone", not any("Idle" in key or "Braking" in key for key in keys))

check("the driver's attributes and the formula, asked with the driver, may come after the vehicle is taken",
      all(levers.comes_late(name) for name in ("ReverseSpeed", "MaxAccel", "calc_vehicle_weapon_damage")))
check("the vehicle's own levers come with it or never",
      not any(levers.comes_late(name) for name in ("YawSpring_Boosting", levers.JUMP, levers.DAMAGE_TAKEN)))

other = sdk_stubs.Vehicle("OakVehicle_2")
del other.OakVehicleMovement.HoverSetup.YawSpring_Boosting
other.DriverPawn = None
found, missing = levers.targets(other)
check("a vehicle built otherwise gives what it has and names what it lacks",
      missing == ["YawSpring_Boosting", *ATTRIBUTES, "calc_vehicle_weapon_damage"]
      and [target.key for target in found] == [f"YawSpring_Hovering[{i}]" for i in range(3)]
      + ["PowerslideJumpHeight", "DamageTakenMultiplier.BaseValue", "DamageTakenMultiplier.Value"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
