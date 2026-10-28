"""Tests which vehicle the player drives: none before a player, on foot or while loading; the pawn at the wheel. A
character's class is asked once for the field it lacks; the co-op role's enum is looked up once."""

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


class Walker:
    """A character on foot, of its own class, counting how often it is asked for the field it lacks."""

    def __init__(self, cls: sdk_stubs.FakeClass) -> None:
        self.Name = "OakCharacter_2"
        self.Class = cls
        self.asked = 0

    def __getattr__(self, name: str) -> object:
        if name == "OakVehicleMovement":
            self.asked += 1
        raise AttributeError(name)


def seated(pawn: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(Pawn=pawn)


state = sdk_stubs.install()
unrealsdk = sys.modules["unrealsdk"]

from vehicle_driving import seat  # noqa: E402

check("before a player exists, no vehicle", seat.driven_vehicle(None) is None)
check("while loading, no pawn and no vehicle", seat.driven_vehicle(seated(None)) is None)
check("on foot, no vehicle", seat.driven_vehicle(seated(sdk_stubs.character())) is None)
car = sdk_stubs.Vehicle()
check("at the wheel, the vehicle", seat.driven_vehicle(seated(car)) is car)
wreck = sdk_stubs.Vehicle()
sdk_stubs.destroy(wreck)
check("a vehicle the game destroyed while still the controller's pawn reads as no vehicle",
      seat.driven_vehicle(seated(wreck)) is None)

walker = Walker(sdk_stubs.FakeClass("BP_Char_Walker"))
answers = [seat.driven_vehicle(seated(walker)) for _ in range(10)]
check("on foot, the character's class is asked once for the field it lacks, then remembered",
      answers == [None] * 10 and walker.asked == 1)
check("a vehicle is still the vehicle at every frame", all(seat.driven_vehicle(seated(car)) is car for _ in range(3)))
building = types.SimpleNamespace(Name="OakVehicle_Building", Class=sdk_stubs.FakeClass("BP_Vehicle"),
                                 OakVehicleMovement=None)
check("a vehicle whose movement is not there yet is no vehicle, and its class is never taken for a character's",
      seat.driven_vehicle(seated(building)) is None and not seat.is_vehicle(building))
building.OakVehicleMovement = car.OakVehicleMovement
check("so it is the vehicle as soon as its movement comes", seat.driven_vehicle(seated(building)) is building)
sdk_stubs.destroy(walker.Class)
seat.driven_vehicle(seated(walker))
check("a class the game destroyed is asked again: another may have taken its place", walker.asked == 2)
for number in range(seat.MAX_FOOT_CLASSES + 5):
    seat.is_vehicle(Walker(sdk_stubs.FakeClass(f"BP_Char_{number}")))
check("the classes remembered are bounded", len(seat._on_foot) <= seat.MAX_FOOT_CLASSES)

lookups: list[str] = []
find_enum = unrealsdk.find_enum
unrealsdk.find_enum = lambda name: lookups.append(name) or find_enum(name)
guest_car = sdk_stubs.Vehicle()
guest_car.role = "ROLE_AutonomousProxy"
roles = [seat.on_guest_game(car), seat.on_guest_game(guest_car), seat.on_guest_game(car)]
unrealsdk.find_enum = find_enum
check("solo or the host, this game has the authority; on a guest's game it has not", roles == [False, True, False])
check("the co-op role's enum is looked up once, not at every call", lookups == ["ENetRole"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
