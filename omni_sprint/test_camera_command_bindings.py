"""Omni Sprint exposes both devices through the existing camera callbacks."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

import omni_sprint  # noqa: E402
from omni_sprint import camera, settings  # noqa: E402

ids = ("third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
       "orbit_key", "orbit_controller")
ids += ("zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller")
assert tuple(option.identifier for option in settings.commands.options) == ids
assert tuple(omni_sprint.mod.kwargs["keybinds"]) == settings.commands.binds
assert settings.commands.defaults()["shoulder_key"] == "Six"
assert settings.commands.defaults()["orbit_key"] == "Seven"

settings.commands.apply({"shoulder_key": "F6"})
settings.commands.align()
assert settings.shoulder_key.value == "F6" and settings.shoulder_bind.key == "F6"
settings.commands.apply(settings.commands.defaults())
settings.commands.apply({
    "third_person_controller": "Gamepad_FaceButton_Top",
    "shoulder_controller": "Gamepad_FaceButton_Left",
    "orbit_controller": "Gamepad_FaceButton_Right",
    "zoom_in_key": "MouseScrollUp", "zoom_out_key": "MouseScrollDown",
    "zoom_in_controller": "Gamepad_LeftShoulder", "zoom_out_controller": "Gamepad_RightShoulder",
})

calls = []
camera.start = camera.stop = lambda: None
camera.toggle_third_person = lambda: calls.append("third_person")
camera.toggle_shoulder = lambda: calls.append("shoulder")
camera.toggle_orbit = lambda: calls.append("orbit")
camera.adjust_orbit_zoom = lambda direction: calls.append(direction)
omni_sprint.mod.enable()
for key in ("P", "Gamepad_FaceButton_Top", "Six", "Gamepad_FaceButton_Left",
            "Seven", "Gamepad_FaceButton_Right"):
    state["keybinds"][key]()
assert calls == ["third_person", "third_person", "shoulder", "shoulder", "orbit", "orbit"]
for key in ("MouseScrollUp", "MouseScrollDown", "Gamepad_LeftShoulder", "Gamepad_RightShoulder"):
    state["keybinds"][key]()
assert calls[-4:] == [-1, 1, -1, 1]
saved = tuple(option.value for option in settings.commands.options)
omni_sprint.mod.disable()
assert tuple(option.value for option in settings.commands.options) == saved
assert not state["keybinds"]
print("RESULTAT: OK | Omni Sprint owns five actions and ten persistent assignments")
