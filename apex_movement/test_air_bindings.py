"""Tests the key bindings: keys found in the game's list, air presses blocked, errors and loading let presses through."""

import importlib
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import air_bindings, air_keys, game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


Block = sys.modules["unrealsdk.hooks"].Block
pressed, released = types.SimpleNamespace(name="IE_Pressed"), types.SimpleNamespace(name="IE_Released")
pad, cross = "Gamepad_FaceButton_Right", "Gamepad_FaceButton_Bottom"

check("crouch keys are read from the game's list",
      air_bindings.keys_for(state["mappings"], air_bindings.CROUCH_ACTIONS) == {"LeftControl", pad})
unnamed = [types.SimpleNamespace(Action=None, Key=types.SimpleNamespace(KeyName="F1"))]
check("a mapping without an action is skipped", air_bindings.keys_for(unnamed, air_bindings.CROUCH_ACTIONS) == set())

check("nothing is bound before bind", not air_bindings.is_bound())
check("bind succeeds with a crouch key", air_bindings.bind(state["mappings"]))
check("every crouch and jump key gets a keybind", set(state["keybinds"]) == {"LeftControl", pad, cross, "SpaceBar"})
check("the bound keys are logged", any("air crouch keys" in line for line in state["misc"]))
check("the keys bound match the game's list", air_bindings.matches(state["mappings"]))
check("a list without the gamepad's crouch no longer matches: read at a vehicle exit, it lacked it (2026-09-18)",
      not air_bindings.matches([m for m in state["mappings"] if m.Key.KeyName != pad]))

player = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, player)
game.refresh(0)
crouch = state["keybinds"][pad]

check("a ground press reaches the game", crouch(pressed) is None)
crouch(released)
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("an air press is blocked", crouch(pressed) is Block)
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
check("its release on the ground is blocked too", crouch(released) is Block)

player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
crouch(pressed)
state["keybinds"][cross](pressed)
check("the jump key feeds the combination", not air_keys.is_held())
air_keys.reset()

player.CharacterMovement = None
check("an unreadable state lets the press through", crouch(pressed) is None)
check("the error is reported once", len(state["errors"]) == 1)
crouch(pressed)
check("a second error is not reported again", len(state["errors"]) == 1)
check("a broken jump event does not raise", state["keybinds"][cross](None) is None)
player.CharacterMovement = sdk_stubs.FakeMovement()

game.forget()
player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("without a player every press passes", crouch(pressed) is None)

air_bindings.unbind()
check("unbind releases every keybind", state["keybinds"] == {} and not air_bindings.is_bound())
check("the release is logged", any("air crouch keys released (4)" in line for line in state["misc"]))
lines = len(state["misc"])
air_bindings.unbind()
check("a second unbind logs nothing", len(state["misc"]) == lines)

check("bind refuses a list without a crouch key", not air_bindings.bind([sdk_stubs.mapping("Action_Jump_HoldToGlide", cross)]))
check("a refused bind binds nothing", state["keybinds"] == {})

# A separate file ships the same code under another package name, as build_movement_files.py does.
separate_package = types.ModuleType("apex_ground_slam")
separate_package.__path__ = [str(HERE / "apex_movement")]
sys.modules["apex_ground_slam"] = separate_package
air_bindings.unbind()
check("released, the keys match no list any more", not air_bindings.matches(state["mappings"]))
separate = importlib.import_module("apex_ground_slam.air_bindings")
separate.bind(state["mappings"])
identifiers = [bound.identifier for bound in separate._binds]
check("a separate file's keybinds carry its own package name",
      identifiers and all(identifier.startswith("apex_ground_slam:") for identifier in identifiers))
separate.unbind()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
