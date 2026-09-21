"""Fake native input registration for capture tests, independent of gameplay keybinds."""

import sys
import types

import sdk_stubs

state = sdk_stubs.install()
state["extra_classes"]["InputSettings"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(ConsoleKeys=[types.SimpleNamespace(KeyName="Tilde")]))
known = {"V", "G", "J", "LeftControl", "SpaceBar", "LeftMouseButton", "RightMouseButton",
         "ThumbMouseButton", "ThumbMouseButton2", "MouseScrollUp", "MouseWheelAxis", "Escape", "Tilde",
         "Gamepad_RightThumbstick", "Gamepad_LeftShoulder", "Gamepad_RightShoulder",
         "Gamepad_FaceButton_Bottom", "Gamepad_LeftTriggerAxis"}
known.update(("Gamepad_FaceButton_Top", "Gamepad_FaceButton_Left", "Gamepad_FaceButton_Right"))
matching = types.ModuleType("console_mod_menu.key_matching")
matching.KNOWN_KEYS = known
sys.modules["console_mod_menu"] = types.ModuleType("console_mod_menu")
sys.modules["console_mod_menu.key_matching"] = matching
from apex_grapple import control_config as config, control_menu, mod
