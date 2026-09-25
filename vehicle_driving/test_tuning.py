"""Tests the owner of the values: set, followed, put back, never multiplied twice, destroyed owners, failures."""

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


def near(a: float, b: float) -> bool:
    return abs(a - b) < 1e-6


class Locked:
    """A value the game refuses to take back once locked."""

    def __init__(self, value: float) -> None:
        self.__dict__.update(constant=value, locked=False)

    def __setattr__(self, name: str, value: float) -> None:
        if self.locked:
            raise RuntimeError("locked")
        self.__dict__[name] = value


sdk_stubs.install()

from vehicle_driving import tuning  # noqa: E402

FACTORS = {"max_speed": 1.25, "acceleration": 2.5, "turn_speed": 2.5, "jump_height": 2.0}
driver = sdk_stubs.Driver()
attributes = driver.VehicleDriverComponent.VehicleAttributesState
car = sdk_stubs.Vehicle("OakVehicle_1", driver)
hover = car.OakVehicleMovement.HoverSetup
owner = tuning.Tuning()

check("nothing is held at first", owner.vehicle() is None and not owner.holds())
lines = owner.take(car)
check("taking a vehicle says so", lines == ["driving OakVehicle_1"] and owner.vehicle() is car and owner.holds())
check("taking writes nothing yet", hover.PowerslideJumpHeight.constant == 165.0)
lines = owner.update(FACTORS)
check("the springs turn harder", [spring.Stiffness for spring in hover.YawSpring_Hovering.Springs] == [7.5, 8.75, 10.0])
check("the speeds and accelerations, base and value",
      attributes.maxspeed.BaseValue == 62.5 and near(attributes.maxspeed.Value, 51.3194 * 1.25)
      and attributes.MaxAccel.BaseValue == 2500.0 and near(attributes.BoostMaxAccel.Value, 1615.08 * 2.5))
check("the jump", hover.PowerslideJumpHeight.constant == 330.0)
check("a first write says what it set, from the game's own values: the proof in the log that nothing is multiplied "
      "twice", len(lines) == 1 and lines[0].startswith("set YawSpring_Hovering[0] 3.000->7.500, ")
      and "maxspeed.BaseValue 50.000->62.500" in lines[0]
      and lines[0].endswith("PowerslideJumpHeight 165.000->330.000"))
check("an update with nothing changed says nothing", owner.update(FACTORS) == [])
check("an update with nothing changed never multiplies twice",
      hover.PowerslideJumpHeight.constant == 330.0 and attributes.MaxAccel.BaseValue == 2500.0)
lines = owner.update(dict(FACTORS, jump_height=4.0))
check("a moved slider writes from the game's original", hover.PowerslideJumpHeight.constant == 660.0
      and lines == ["set PowerslideJumpHeight 165.000->660.000"])
owner.update(dict(FACTORS, jump_height=1.0))
check("at 100 percent the game's own value is back", hover.PowerslideJumpHeight.constant == 165.0)
owner.update(FACTORS)

hover.YawSpring_Boosting.Springs[0].Stiffness = 1.5
lines = owner.update(FACTORS)
check("a spring the game rewrote becomes the original and is multiplied again",
      hover.YawSpring_Boosting.Springs[0].Stiffness == 3.75
      and lines == ["YawSpring_Boosting[0] rewritten by the game to 1.500, taken as its own",
                    "set YawSpring_Boosting[0] 1.500->3.750"])
attributes.MaxAccel.BaseValue, attributes.MaxAccel.Value = 1000.0, 1400.0
lines = owner.update(FACTORS)
check("an attribute the game reset, base and value, is taken again from its new values",
      attributes.MaxAccel.BaseValue == 2500.0 and attributes.MaxAccel.Value == 3500.0 and len(lines) == 3)
attributes.maxspeed.Value = 64.0
lines = owner.update(FACTORS)
check("a value the game recomputed from the mod's base is left to it: taken as its own it would be multiplied twice",
      attributes.maxspeed.Value == 64.0 and lines == ["maxspeed.Value recomputed by the game to 64.000, left to it"])
check("and it is not reported again", owner.update(FACTORS) == [])

lines = owner.put_back()
check("put back: the game's values, the ones it rewrote included",
      [spring.Stiffness for spring in hover.YawSpring_Hovering.Springs] == [3.0, 3.5, 4.0]
      and hover.YawSpring_Boosting.Springs[0].Stiffness == 1.5 and attributes.MaxAccel.BaseValue == 1000.0
      and attributes.MaxAccel.Value == 1400.0 and attributes.maxspeed.BaseValue == 50.0
      and hover.PowerslideJumpHeight.constant == 165.0)
check("nothing failed and nothing is held any more", lines == [] and owner.vehicle() is None and not owner.holds())

owner.take(car)
owner.update(FACTORS)
owner.put_back()
owner.take(car)
owner.update(FACTORS)
check("the same vehicle taken again is never multiplied twice",
      hover.PowerslideJumpHeight.constant == 330.0 and attributes.MaxAccel.BaseValue == 2500.0)

second = sdk_stubs.Vehicle("OakVehicle_2", driver)
lines = owner.take(second)
check("taking another vehicle puts the first one back first",
      hover.PowerslideJumpHeight.constant == 165.0 and attributes.MaxAccel.BaseValue == 1000.0
      and lines == ["driving OakVehicle_2"])
owner.update(FACTORS)
sdk_stubs.destroy(second)
second.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant = 999.0
check("a destroyed vehicle is no longer the one held, but its driver still is",
      owner.vehicle() is None and owner.holds())
owner.put_back()
check("a destroyed vehicle is never written again, and its driver still gets the game's values back",
      second.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant == 999.0
      and attributes.MaxAccel.BaseValue == 1000.0)

bare = sdk_stubs.Vehicle("OakVehicle_3", driver)
del bare.OakVehicleMovement.HoverSetup.PowerslideJumpHeight
lines = owner.take(bare)
check("a lever the vehicle lacks is named and left to the game",
      lines == ["driving OakVehicle_3", "PowerslideJumpHeight not found on OakVehicle_3: left to the game"])
owner.update(FACTORS)
check("the other levers still work", bare.OakVehicleMovement.HoverSetup.YawSpring_Hovering.Springs[0].Stiffness == 7.5)
owner.put_back()

stuck = sdk_stubs.Vehicle("OakVehicle_4", driver)
stuck.OakVehicleMovement.HoverSetup.PowerslideJumpHeight = Locked(165.0)
owner.take(stuck)
owner.update(FACTORS)
stuck.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.locked = True
lines = owner.put_back()
check("a value that cannot be put back is reported, and the others still go back",
      lines == ["could not put back PowerslideJumpHeight: RuntimeError('locked')"]
      and attributes.MaxAccel.BaseValue == 1000.0 and not owner.holds())

late = sdk_stubs.Vehicle("OakVehicle_5", driver)
late.DriverPawn = None
owner.take(late)
owner.update(FACTORS)
check("a driver not yet seated when the vehicle is taken: the vehicle's own levers are set at once",
      late.OakVehicleMovement.HoverSetup.YawSpring_Hovering.Springs[0].Stiffness == 7.5
      and attributes.MaxAccel.BaseValue == 1000.0)
late.DriverPawn = driver
lines = owner.update(FACTORS)
check("the driver's speed and acceleration are set at the first check once the driver is seated",
      attributes.MaxAccel.BaseValue == 2500.0 and near(attributes.maxspeed.Value, 51.3194 * 1.25))
check("the log names what was found late", any("found on OakVehicle_5" in line for line in lines))
check("the vehicle's levers written before are not written twice",
      late.OakVehicleMovement.HoverSetup.YawSpring_Hovering.Springs[0].Stiffness == 7.5)
owner.put_back()
check("everything goes back at the descent, the late driver's values too",
      attributes.MaxAccel.BaseValue == 1000.0 and attributes.maxspeed.BaseValue == 50.0
      and late.OakVehicleMovement.HoverSetup.YawSpring_Hovering.Springs[0].Stiffness == 3.0)

alone = sdk_stubs.Vehicle("OakVehicle_6", driver)
alone.DriverPawn = None
owner.take(alone)
owner.update(FACTORS)
check("a driver that never comes adds no line at each check", owner.update(FACTORS) == [])
owner.put_back()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
