"""The full pack exposes both devices through the existing camera callbacks."""

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

ids = ("third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
       "orbit_key", "orbit_controller")
ids += ("zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller")
assert tuple(option.identifier for option in camera_settings.commands.options) == ids
assert tuple(apex_movement.camera_keybinds) == camera_settings.commands.binds
assert camera_settings.commands.defaults()["shoulder_key"] == "Six"
assert camera_settings.commands.defaults()["orbit_key"] == "Seven"

camera_settings.commands.apply({"orbit_key": "F7"})
camera_settings.commands.align()
assert camera_settings.orbit_key.value == "F7" and camera_settings.orbit_bind.key == "F7"
camera_settings.commands.apply(camera_settings.commands.defaults())
camera_settings.commands.apply({
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
apex_movement.mod.enable()
for key in ("P", "Gamepad_FaceButton_Top", "Six", "Gamepad_FaceButton_Left",
            "Seven", "Gamepad_FaceButton_Right"):
    state["keybinds"][key]()
assert calls == ["third_person", "third_person", "shoulder", "shoulder", "orbit", "orbit"]
for key in ("MouseScrollUp", "MouseScrollDown", "Gamepad_LeftShoulder", "Gamepad_RightShoulder"):
    state["keybinds"][key]()
assert calls[-4:] == [-1, 1, -1, 1]
saved = tuple(option.value for option in camera_settings.commands.options)
apex_movement.mod.disable()
assert tuple(option.value for option in camera_settings.commands.options) == saved
assert not any(key.startswith("Gamepad_") for key in state["keybinds"])
print("RESULTAT: OK | Apex Movement owns five actions and ten persistent assignments")
