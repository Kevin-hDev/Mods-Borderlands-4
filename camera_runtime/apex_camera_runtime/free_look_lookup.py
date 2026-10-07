"""Free Look finds the third-person, Orbit and first-person camera mode definitions in the running game.

The offsets come from the SDK's own types, and each mode's name from a struct of our own, as the game keeps it
(free_look_definitions.py). Memory goes through process_memory.py, so a wrong address fails instead of crashing.
Found by the probe in about 0.06 s, its start included (journal of 2026-10-07, trial 15); looked up once per game,
then each definition is read again before any write.
"""

from typing import Any, NamedTuple

from . import free_look_definitions as defs

STORE_TYPE = "NexusConfigStoreCameraMode"
STORE_WINDOW = 0x400
KEY_TYPE, KEY_FIELD = "DefaultCameraModeConfig", "cameramodename"
# Bounds against a list that never ends, far above the game's own counts.
MAX_STRUCTS = 200_000
MAX_STORES = 8


class Modes(NamedTuple):
    shape: defs.Layout
    addresses: dict


def _offsets(sdk: Any, type_name: str) -> dict:
    for index, found in enumerate(sdk.find_all("ScriptStruct", exact=False)):
        if index >= MAX_STRUCTS:
            break
        if str(found.Name) == type_name:
            return {str(prop.Name).lower(): int(prop.Offset_Internal) for prop in found._properties()}
    raise LookupError(f"{type_name} type not found")


def _name_keys(sdk: Any, memory: Any) -> dict:
    offset = _offsets(sdk, KEY_TYPE)[KEY_FIELD]
    keys = {}
    for name in defs.NAMES:
        holder = sdk.make_struct(KEY_TYPE, CameraModeName=name)
        keys[name] = memory.read(holder._get_address() + offset, 8)
    return keys


def mode_at(memory: Any, address: int, shape: defs.Layout) -> "defs.Mode | None":
    data = memory.read(address, shape.size)
    return None if data is None else defs.read_mode(data, shape)


def find(sdk: Any, memory: Any) -> Modes:
    """The three definitions, or LookupError saying why they cannot be trusted."""
    offsets = _offsets(sdk, defs.TYPE_NAME)
    shape = defs.Layout(offsets[defs.BLEND], offsets[defs.METHOD], offsets[defs.BEHAVIORS])
    keys = _name_keys(sdk, memory)
    stores = [item for item in sdk.find_all(STORE_TYPE, exact=False) if not str(item.Name).startswith("Default__")]
    for store in stores[:MAX_STORES]:
        for _offset, address in defs.slots(memory.read(int(store._get_address()), STORE_WINDOW) or b""):
            rows = defs.entries(memory.read(address, defs.ENTRY * defs.MAX_ENTRIES) or b"")
            if sum(1 for _head, value in rows if mode_at(memory, value, shape)) < defs.MIN_FOUND:
                continue
            addresses = defs.named(rows, keys)
            modes = {name: mode_at(memory, value, shape) for name, value in addresses.items()}
            refusal = defs.trusted({name: mode for name, mode in modes.items() if mode})
            if refusal is not None:
                raise LookupError(f"camera mode table not trusted: {refusal}")
            return Modes(shape, addresses)
    raise LookupError("camera mode table not found")
