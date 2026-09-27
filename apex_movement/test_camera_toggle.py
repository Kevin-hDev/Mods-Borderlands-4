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
        self.accept_menu = True

    def register(self, *args):
        self.registered.append(args)

    def unregister(self, _owner):
        pass

    def toggle_third_person(self, owner):
        self.toggles.append(("third_person", owner))
        settings = self.registered[0][2]
        settings.set_third_person(not settings.third_person_enabled())
        return True

    def toggle_shoulder(self, owner):
        self.toggles.append(("shoulder", owner))
        settings = self.registered[0][2]
        settings.set_shoulder_left(not settings.shoulder_left())
        return True

    def toggle_orbit(self, owner):
        self.toggles.append(("orbit", owner))
        settings = self.registered[0][2]
        settings.set_orbit(not settings.orbit_enabled())
        return True

    def set_shoulder(self, owner, left):
        self.toggles.append(("shoulder_menu", owner, left))
        if not self.accept_menu:
            return False
        self.registered[0][2].set_shoulder_left(left)
        return True

    def set_orbit(self, owner, enabled):
        self.toggles.append(("orbit_menu", owner, enabled))
        if not self.accept_menu:
            return False
        self.registered[0][2].set_orbit(enabled)
        return True

    def camera_ready(self, _owner):
        return True


runtime = Runtime()
camera.shared = lambda: runtime

ok = camera_settings.third_person_key.default_value == "P"
ok = ok and camera_settings.shoulder_key.default_value == "Six"
ok = ok and camera_settings.orbit_key.default_value == "Seven"
ok = ok and camera_settings.shoulder_left.value is False and camera_settings.orbit.value is False
ok = ok and all(bind in apex_movement.mod.kwargs["keybinds"] for bind in
                (camera_settings.third_person_bind, camera_settings.shoulder_bind,
                 camera_settings.orbit_bind))
# The SDK lists a visible bind again under "Keybinds": hidden, the key has the option as its one entry (Kevin).
ok = ok and camera_settings.third_person_bind.is_hidden is True and camera_settings.third_person_key.is_hidden is False
apex_movement.mod.enable()
ok = ok and "P" in state["keybinds"]
state["keybinds"]["P"]()
state["keybinds"]["Six"]()
state["keybinds"]["Seven"]()
ok = ok and runtime.toggles == [("third_person", "apex_movement"),
                                ("shoulder", "apex_movement"),
                                ("orbit", "apex_movement")]
ok = ok and camera_settings.third_person.value is True and state["settings_saves"] == 3
ok = ok and camera_settings.shoulder_left.value is True and camera_settings.orbit.value is True
camera_settings.shoulder_left.value = False
camera_settings.orbit.value = False
ok = ok and runtime.toggles[-2:] == [("shoulder_menu", "apex_movement", False),
                                     ("orbit_menu", "apex_movement", False)]
ok = ok and camera_settings.shoulder_left.value is False and camera_settings.orbit.value is False
runtime.accept_menu = False
camera_settings.shoulder_left.value = True
camera_settings.orbit.value = True
ok = ok and camera_settings.shoulder_left.value is False and camera_settings.orbit.value is False
class RefusingMod:
    def save_settings(self):
        raise RuntimeError("save refused")


camera_settings.shoulder_left.mod = RefusingMod()
camera_settings.orbit.mod = RefusingMod()
try:
    camera_settings.set_shoulder_left(True)
except RuntimeError:
    pass
try:
    camera_settings.set_orbit(True)
except RuntimeError:
    pass
ok = ok and camera_settings.shoulder_left.value is False and camera_settings.orbit.value is False
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
for option in (camera_settings.shoulder_key, camera_settings.orbit_key):
    option.value = "ThumbMouseButton"
    ok = ok and option.value == "ThumbMouseButton" and "ThumbMouseButton" in state["keybinds"]
    for raw in ("Escape", "Tilde", "Gamepad_FaceButton_Top"):
        option.value = raw
        ok = ok and option.value is None and raw not in state["keybinds"]
apex_movement.mod.disable()
ok = ok and "K" not in state["keybinds"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
