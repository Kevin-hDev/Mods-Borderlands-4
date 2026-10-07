"""Omni Sprint owns the shortcut when it is the elected camera mod."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import omni_sprint  # noqa: E402
from omni_sprint import camera, settings  # noqa: E402
from apex_camera_runtime.keyboard_layout import TOP_ROW_SEVEN, TOP_ROW_SIX, key_at  # noqa: E402
SIX, SEVEN = key_at(TOP_ROW_SIX, "Six"), key_at(TOP_ROW_SEVEN, "Seven")


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
        chosen = self.registered[0][2]
        chosen.set_third_person(not chosen.third_person_enabled())
        return True

    def toggle_shoulder(self, owner):
        self.toggles.append(("shoulder", owner))
        chosen = self.registered[0][2]
        chosen.set_shoulder_left(not chosen.shoulder_left())
        return True

    def toggle_orbit(self, owner):
        self.toggles.append(("orbit", owner))
        chosen = self.registered[0][2]
        chosen.set_orbit(not chosen.orbit_enabled())
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

ok = settings.third_person_key.default_value == "P"
ok = ok and settings.shoulder_key.default_value == SIX and settings.orbit_key.default_value == SEVEN
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
ok = ok and all(bind in omni_sprint.mod.kwargs["keybinds"] for bind in
                (settings.third_person_bind, settings.shoulder_bind, settings.orbit_bind))
# The SDK lists a visible bind again under "Keybinds": hidden, the key has the option as its one entry (Kevin).
ok = ok and settings.third_person_bind.is_hidden is True and settings.third_person_key.is_hidden is False
omni_sprint.mod.enable()
state["keybinds"]["P"]()
state["keybinds"][SIX]()
state["keybinds"][SEVEN]()
ok = ok and runtime.toggles == [("third_person", "omni_sprint"),
                                ("shoulder", "omni_sprint"),
                                ("orbit", "omni_sprint")]
ok = ok and settings.third_person.value is True and state["settings_saves"] == 3
ok = ok and settings.shoulder_left.value is True and settings.orbit.value is True
settings.shoulder_left.value = False
settings.orbit.value = False
ok = ok and runtime.toggles[-2:] == [("shoulder_menu", "omni_sprint", False),
                                     ("orbit_menu", "omni_sprint", False)]
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
runtime.accept_menu = False
settings.shoulder_left.value = True
settings.orbit.value = True
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
class RefusingMod:
    def save_settings(self):
        raise RuntimeError("save refused")


settings.shoulder_left.mod = RefusingMod()
settings.orbit.mod = RefusingMod()
try:
    settings.set_shoulder_left(True)
except RuntimeError:
    pass
try:
    settings.set_orbit(True)
except RuntimeError:
    pass
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
settings.third_person_key.value = "O"
omni_sprint.mod.save_settings()
ok = ok and "P" not in state["keybinds"] and "O" in state["keybinds"]
settings.third_person_key.value = "Gamepad_FaceButton_Top"
ok = ok and settings.third_person_key.value is None and "Gamepad_FaceButton_Top" not in state["keybinds"]
for option in (settings.shoulder_key, settings.orbit_key):
    option.value = "ThumbMouseButton"
    ok = ok and option.value == "ThumbMouseButton" and "ThumbMouseButton" in state["keybinds"]
    for raw in ("Escape", "Tilde", "Gamepad_FaceButton_Top"):
        option.value = raw
        ok = ok and option.value is None and raw not in state["keybinds"]
omni_sprint.mod.disable()
ok = ok and "O" not in state["keybinds"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
