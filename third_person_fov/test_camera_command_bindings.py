"""The standalone owner exposes and preserves five actions and ten assignments."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

import third_person_fov  # noqa: E402
from third_person_fov import camera, settings  # noqa: E402

ids = (
    "third_person_key", "third_person_controller",
    "shoulder_key", "shoulder_controller", "orbit_key", "orbit_controller",
)
ids += ("zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller")
assert tuple(option.identifier for option in settings.commands.options) == ids
assert settings.commands.defaults() == {
    "third_person_key": "P", "third_person_controller": None,
    "shoulder_key": "Six", "shoulder_controller": None,
    "orbit_key": "Seven", "orbit_controller": None,
    "zoom_in_key": None, "zoom_in_controller": None,
    "zoom_out_key": None, "zoom_out_controller": None,
}
assert tuple(third_person_fov.mod.kwargs["keybinds"]) == settings.commands.binds

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
third_person_fov.mod.enable()
for key in ("P", "Gamepad_FaceButton_Top", "Six", "Gamepad_FaceButton_Left",
            "Seven", "Gamepad_FaceButton_Right"):
    state["keybinds"][key]()
assert calls == ["third_person", "third_person", "shoulder", "shoulder", "orbit", "orbit"]
for key in ("MouseScrollUp", "MouseScrollDown", "Gamepad_LeftShoulder", "Gamepad_RightShoulder"):
    state["keybinds"][key]()
assert calls[-4:] == [-1, 1, -1, 1]
saved = tuple(option.value for option in settings.commands.options)
third_person_fov.mod.disable()
assert not state["keybinds"] and tuple(option.value for option in settings.commands.options) == saved
print("RESULTAT: OK | Third Person & FOV owns five actions and ten persistent assignments")
