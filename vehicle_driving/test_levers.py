"""Tests the levers: what each setting multiplies on Kevin's vehicle, its weapons, and a vehicle built otherwise."""

import pathlib
import sys
import types

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
check("then the jump, the damage the vehicle takes and each weapon's damage per shot",
      keys[18:] == ["PowerslideJumpHeight", "DamageTakenMultiplier.BaseValue", "DamageTakenMultiplier.Value"]
      + [f"weapon[{i}].damage.{field}" for i in range(4) for field in PAIR])
check("nothing is missing on Kevin's vehicle", missing == [])
by_key = {target.key: target for target in found}
check("each lever follows its setting",
      by_key["YawSpring_Boosting[1]"].setting == "turn_speed" and by_key["BoostMaxSpeed.Value"].setting == "max_speed"
      and by_key["MaxAccel.BaseValue"].setting == "acceleration"
      and by_key["PowerslideJumpHeight"].setting == "jump_height"
      and by_key["ReverseSpeed.Value"].setting == "reverse_speed"
      and by_key["BoostConsumptionRateScalar.BaseValue"].setting == "boost_cost"
      and by_key["DamageTakenMultiplier.Value"].setting == "damage_taken"
      and by_key["weapon[3].damage.Value"].setting == "weapon_damage")
check("a value names its base, and nothing else names one",
      by_key["MaxAccel.Value"].base_key == "MaxAccel.BaseValue" and by_key["MaxAccel.BaseValue"].base_key is None
      and by_key["weapon[0].damage.Value"].base_key == "weapon[0].damage.BaseValue"
      and by_key["PowerslideJumpHeight"].base_key is None and by_key["YawSpring_Hovering[0]"].base_key is None)
check("each value names the game object that carries it: the vehicle, its driver, or one weapon's firing behavior",
      by_key["YawSpring_Hovering[0]"].owner == levers.VEHICLE and by_key["YawSpring_Hovering[0]"].source is car
      and by_key["maxspeed.Value"].owner == levers.DRIVER and by_key["maxspeed.Value"].source is car.DriverPawn
      and by_key["DamageTakenMultiplier.Value"].owner == levers.VEHICLE
      and by_key["DamageTakenMultiplier.Value"].source is car
      and by_key["weapon[2].damage.Value"].owner == "weapon[2]"
      and by_key["weapon[2].damage.Value"].source is car.VehicleWeapons[2].behaviors[0])
check("a shot's damage: 2.8 for the machine gun, 7 for a rocket (session 11)",
      by_key["weapon[0].damage.Value"].holder.Value == 2.8
      and by_key["weapon[3].damage.BaseValue"].holder.BaseValue == 7.0)
spring = by_key["YawSpring_Hovering[1]"]
check("a lever points at the live value", getattr(spring.holder, spring.field) == 3.5)
check("the idle spring and the braking are left alone", not any("Idle" in key or "Braking" in key for key in keys))

shuffled = sdk_stubs.Vehicle("OakVehicle_3")
shuffled.VehicleWeapons[1].behaviors.reverse()
shuffled.VehicleWeapons[2].behaviors = [sdk_stubs.Behavior("Sight")]
found, missing = levers.targets(shuffled)
by_key = {target.key: target for target in found}
check("the firing behavior is found by its type, wherever it sits",
      by_key["weapon[1].damage.Value"].source is shuffled.VehicleWeapons[1].behaviors[-1])
check("a weapon without one is named and left to the game",
      missing == ["weapon[2].damage"] and "weapon[2].damage.Value" not in by_key)
deep = sdk_stubs.Vehicle("OakVehicle_4")
deep.VehicleWeapons = [types.SimpleNamespace(behaviors=[sdk_stubs.Behavior("Sight")] * levers.MAX_BEHAVIORS
                                             + [sdk_stubs.Behavior("FireProjectile", 2.8)])]
check("behaviors past the bound are not searched", levers.targets(deep)[1] == ["weapon[0].damage"])
crowded = sdk_stubs.Vehicle("OakVehicle_5")
crowded.VehicleWeapons = [sdk_stubs.weapon(2.8) for _ in range(20)]
check("weapons past the bound are left alone",
      sum(target.key.endswith(".damage.Value") for target in levers.targets(crowded)[0]) == levers.MAX_WEAPONS)
unarmed = sdk_stubs.Vehicle("OakVehicle_6")
unarmed.VehicleWeapons = []
check("a vehicle without weapons names them", levers.targets(unarmed)[1] == [levers.WEAPONS])
del unarmed.VehicleWeapons
check("and so does one without the field", levers.targets(unarmed)[1] == [levers.WEAPONS])

check("the driver's attributes, the weapons and each weapon's damage may come after the vehicle is taken",
      all(levers.comes_late(name) for name in ("ReverseSpeed", "MaxAccel", levers.WEAPONS, "weapon[2].damage")))
check("the vehicle's own levers come with it or never",
      not any(levers.comes_late(name) for name in ("YawSpring_Boosting", levers.JUMP, levers.DAMAGE_TAKEN)))

other = sdk_stubs.Vehicle("OakVehicle_2")
del other.OakVehicleMovement.HoverSetup.YawSpring_Boosting
other.DriverPawn = None
found, missing = levers.targets(other)
check("a vehicle built otherwise gives what it has and names what it lacks",
      missing == ["YawSpring_Boosting", *ATTRIBUTES]
      and [target.key for target in found] == [f"YawSpring_Hovering[{i}]" for i in range(3)]
      + ["PowerslideJumpHeight", "DamageTakenMultiplier.BaseValue", "DamageTakenMultiplier.Value"]
      + [f"weapon[{i}].damage.{field}" for i in range(4) for field in PAIR])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
