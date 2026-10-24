"""A character's class without a vehicle field is asked once; a vehicle's field is read each time."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.vehicle_field import MAX_CLASSES, VehicleField  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Character:
    """A pawn without the field: each question raises, as the SDK does, and is counted."""

    def __init__(self, class_address):
        self.Class = types.SimpleNamespace(address=class_address)
        self.asked = 0

    def __getattr__(self, name):
        if name == "OakVehicleMovement":
            self.__dict__["asked"] += 1
        raise AttributeError(name)


def weak(item):
    """The SDK's weak pointer: the object while it lives, None once the game has destroyed it."""
    return lambda: None if getattr(item, "gone", False) else item


field = VehicleField(lambda item: item.address, weak)
hunter = Character(0x100)
for _ in range(5):
    check_value = field.movement(hunter)
check("a character is no vehicle", check_value is None)
check("its class is asked once, not at every frame", hunter.asked == 1)
other_body = Character(0x100)
field.movement(other_body)
check("another character of the same class is not asked either", other_body.asked == 0)

movement = object()
car = types.SimpleNamespace(Class=types.SimpleNamespace(address=0x200), OakVehicleMovement=None)
check("a vehicle being built has no movement yet", field.movement(car) is None)
car.OakVehicleMovement = movement
check("its movement is read once built: a vehicle's field is never kept as missing", field.movement(car) is movement)

# Review of 2026-10-24: a character's class unloaded (another save, the title screen), a vehicle's class built at
# its address. The same address is not the same class.
unloaded = Character(0x300)
field.movement(unloaded)
unloaded.Class.gone = True
rebuilt = types.SimpleNamespace(Class=types.SimpleNamespace(address=0x300), OakVehicleMovement=movement)
check("a vehicle whose class took an unloaded character class's place is still a vehicle",
      field.movement(rebuilt) is movement)

no_class = types.SimpleNamespace(OakVehicleMovement=movement)
check("a pawn whose class cannot be read is asked directly", field.movement(no_class) is movement)

for index in range(MAX_CLASSES + 1):
    field.movement(Character(0x1000 + index))
check("the classes kept stay bounded", len(field.without) <= MAX_CLASSES)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
