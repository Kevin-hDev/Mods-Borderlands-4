"""The camera shortcut follows the full pack lifecycle and its saved key."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

import apex_movement  # noqa: E402
from apex_movement import camera, camera_settings  # noqa: E402


class Runtime:
    def __init__(self):
        self.registered = []
        self.toggles = []

    def register(self, *args):
        self.registered.append(args)

    def unregister(self, _owner):
        pass

    def toggle_third_person(self, owner):
        self.toggles.append(owner)
        settings = self.registered[0][2]
        settings.set_third_person(not settings.third_person_enabled())
        return True


runtime = Runtime()
camera.shared = lambda: runtime

ok = camera_settings.third_person_key.default_value == "P"
ok = ok and camera_settings.third_person_bind in apex_movement.mod.kwargs["keybinds"]
apex_movement.mod.enable()
ok = ok and "P" in state["keybinds"]
state["keybinds"]["P"]()
ok = ok and runtime.toggles == ["apex_movement"]
ok = ok and camera_settings.third_person.value is True and state["settings_saves"] == 1
camera_settings.third_person_key.value = "K"
apex_movement.mod.save_settings()
ok = ok and "P" not in state["keybinds"] and "K" in state["keybinds"]
camera_settings.third_person_key.value = "Gamepad_FaceButton_Top"
ok = ok and camera_settings.third_person_key.value is None and "Gamepad_FaceButton_Top" not in state["keybinds"]
camera_settings.third_person_key.value = "Tilde"
ok = ok and camera_settings.third_person_key.value is None and "Tilde" not in state["keybinds"]
camera_settings.third_person_key.value = "MouseX"
ok = ok and camera_settings.third_person_key.value is None and "MouseX" not in state["keybinds"]
camera_settings.third_person_key.value = "LeftMouseButton"
ok = ok and camera_settings.third_person_key.value is None and "LeftMouseButton" not in state["keybinds"]
apex_movement.mod.disable()
ok = ok and "K" not in state["keybinds"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
