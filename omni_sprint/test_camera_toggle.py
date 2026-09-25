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
        chosen = self.registered[0][2]
        chosen.set_third_person(not chosen.third_person_enabled())
        return True


runtime = Runtime()
camera.shared = lambda: runtime

ok = settings.third_person_key.default_value == "P"
ok = ok and settings.third_person_bind in omni_sprint.mod.kwargs["keybinds"]
# The SDK lists a visible bind again under "Keybinds": hidden, the key has the option as its one entry (Kevin).
ok = ok and settings.third_person_bind.is_hidden is True and settings.third_person_key.is_hidden is False
omni_sprint.mod.enable()
state["keybinds"]["P"]()
ok = ok and runtime.toggles == ["omni_sprint"]
ok = ok and settings.third_person.value is True and state["settings_saves"] == 1
settings.third_person_key.value = "O"
omni_sprint.mod.save_settings()
ok = ok and "P" not in state["keybinds"] and "O" in state["keybinds"]
settings.third_person_key.value = "Gamepad_FaceButton_Top"
ok = ok and settings.third_person_key.value is None and "Gamepad_FaceButton_Top" not in state["keybinds"]
omni_sprint.mod.disable()
ok = ok and "O" not in state["keybinds"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
