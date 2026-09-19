"""Tests the definition: offsets from the SDK's type, recognition by its values, the search from the component."""

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


state = sdk_stubs.install()

from omni_sprint import definition, memory  # noqa: E402

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch_memory(memory, fake)

shape = definition.layout()
check("every known value is found in the type, whatever the case of its name",
      shape is not None and len(shape.offsets) == len(definition.KNOWN) and shape.limit == 580)
check("a field the mod does not know is left out", "bcanclimbladders" not in shape.offsets)

partial = sdk_stubs.movement_type()
fields = [field for field in partial._properties() if field.Name != "LadderFriction"]
state["types"] = [types.SimpleNamespace(Name="OakCharacterMovementDef", _properties=lambda: iter(fields))]
check("a type missing one known value gives no layout", definition.layout() is None)
state["types"] = []
check("no type gives no layout", definition.layout() is None)

COMPONENT = sdk_stubs.BASE + 0x1000
DEFINITION = sdk_stubs.BASE + 0x20000
LOOKALIKE = sdk_stubs.BASE + 0x21000
fake.put_definition(DEFINITION, definition.KNOWN)
fake.put_definition(LOOKALIKE, definition.KNOWN)
fake.put_float(LOOKALIKE + sdk_stubs.OFFSETS["LadderFriction"], 9.0)
fake.put_pointer(COMPONENT + 0x40, LOOKALIKE)
fake.put_pointer(COMPONENT + 0x48, 0xDEAD_0000_0000_0000)
fake.put_pointer(COMPONENT + 0x50, 0x10)
fake.put_pointer(COMPONENT + 0x1CF0, DEFINITION)

check("the definition is recognised by its values", definition.recognised(DEFINITION, shape))
check("a block with one value off is not", not definition.recognised(LOOKALIKE, shape))
check("an unreadable block is not", not definition.recognised(0x10, shape))
found = definition.find(COMPONENT, shape)
check("the definition is found from the movement component, past lookalikes and bad pointers",
      found == definition.Found(DEFINITION, 0x1CF0))

fake.put_float(DEFINITION + 580, 180.0)
check("an opened limit is still recognised", definition.recognised(DEFINITION, shape))
fake.put_float(DEFINITION + 580, 400.0)
check("a limit that is not an angle is not", not definition.recognised(DEFINITION, shape))
check("so the component leads nowhere", definition.find(COMPONENT, shape) is None)
check("an unreadable component leads nowhere", definition.find(0x10, shape) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
