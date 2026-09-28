"""Tests the narrow guard which mutes only the native held-crouch slam action."""

import copy
import importlib
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

try:
    slam_hold = importlib.import_module("apex_movement.slam_hold")
except ModuleNotFoundError:
    slam_hold = None

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class MappingArray:
    """Returns struct copies like Unreal; a change persists only when assigned back."""

    def __init__(self, entries: list[types.SimpleNamespace]) -> None:
        self.entries = entries
        self.writes: list[int] = []

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, index: int) -> types.SimpleNamespace:
        return copy.deepcopy(self.entries[index])

    def __setitem__(self, index: int, entry: types.SimpleNamespace) -> None:
        self.entries[index] = copy.deepcopy(entry)
        self.writes.append(index)


def mapping(action: str, key: str, ignored: bool = False) -> types.SimpleNamespace:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action),
                                 Key=types.SimpleNamespace(KeyName=key), bShouldBeIgnored=ignored)


check("the native slam guard module exists", slam_hold is not None)

if slam_hold is not None:
    pad = "Gamepad_FaceButton_Right"
    mappings = MappingArray([
        mapping("Action_CrouchOrDash", pad),
        mapping("Action_Crouch_Hold", pad),
        mapping("Action_Crouch_Hold", "LeftControl", ignored=True),
    ])
    pc = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(EnhancedActionMappings=mappings))
    slam_hold.game.controller = lambda: pc

    slam_hold.update({pad})
    check("only the held key's native hold action is muted",
          [entry.bShouldBeIgnored for entry in mappings.entries] == [False, True, True])

    mappings.entries[1].bShouldBeIgnored = False
    slam_hold.update({pad})
    check("the guard reapplies the mute after the game rebuilds it", mappings.entries[1].bShouldBeIgnored)

    slam_hold.update(set())
    check("release restores each mapping's original state",
          [entry.bShouldBeIgnored for entry in mappings.entries] == [False, False, True])

    slam_hold.update({"LeftControl"})
    slam_hold.release()
    check("shutdown preserves a mapping that was already ignored", mappings.entries[2].bShouldBeIgnored)

    slam_hold.game.controller = lambda: None
    check("loading without a controller is a normal no-op", not slam_hold.update({pad}))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
