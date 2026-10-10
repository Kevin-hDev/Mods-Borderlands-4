"""Checks six camera actions and twelve assignments as one grouped authority; Free Look's keys are read each frame,
its binds call nothing."""

import pathlib
import sys
import types


class FakeBind:
    def __init__(self, identifier, key, callback, **kwargs):
        self.identifier, self.key, self.callback = identifier, key, callback
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)
        self.event_filter = kwargs.get("event_filter", "missing")


class FakeKeybindOption:
    @classmethod
    def from_keybind(cls, bind):
        option = cls()
        option.identifier = bind.identifier
        option.default_value = bind.key
        option.display_name = bind.display_name
        option.description = bind.description
        option.is_hidden = bind.is_hidden
        option._bind = bind
        option.value = bind.key
        return option

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == "value" and getattr(self, "_bind", None) is not None:
            self._bind.key = value


mods_base = types.ModuleType("mods_base")
mods_base.KeybindOption = FakeKeybindOption
mods_base.EInputEvent = types.SimpleNamespace(IE_Pressed="IE_Pressed")
mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeBind(
    identifier, key, callback, **kwargs)
sys.modules["mods_base"] = mods_base
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from apex_camera_runtime.camera_commands import CameraCommands  # noqa: E402
from apex_camera_runtime.keyboard_layout import (RIGHT_OF_TAB, TOP_ROW_EIGHT, TOP_ROW_SEVEN, TOP_ROW_SIX,  # noqa: E402
                                                 key_at)
FREE_LOOK, SIX, SEVEN = key_at(RIGHT_OF_TAB, "Q"), key_at(TOP_ROW_SIX, "Six"), key_at(TOP_ROW_SEVEN, "Seven")
EIGHT = key_at(TOP_ROW_EIGHT, "Eight")


calls = []


def callback(name):
    return lambda: calls.append(name)


commands = CameraCommands(
    third_person=callback("third_person"),
    shoulder=callback("shoulder"),
    orbit=callback("orbit"),
    zoom_in=callback("zoom_in"),
    zoom_out=callback("zoom_out"),
    camera_distance=callback("camera_distance"),
)
identifiers = (
    "third_person_key", "third_person_controller",
    "shoulder_key", "shoulder_controller",
    "orbit_key", "orbit_controller",
    "zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller",
    "free_look_key", "free_look_controller",
    "camera_distance_key", "camera_distance_controller",
    "sniper_zoom_key", "sniper_zoom_controller",
)
assert tuple(option.identifier for option in commands.options) == identifiers
assert tuple(bind.identifier for bind in commands.binds) == identifiers
# The SDK's text menu lists every entry by its name: each says its device, none shares another's (review, 2026-09-26).
names = [option.display_name for option in commands.options]
assert len(set(names)) == len(names)
assert names[:2] == ["Keyboard: Toggle Third Person", "Controller: Toggle Third Person"]
assert all(name.startswith("Keyboard: " if identifier.endswith("_key") else "Controller: ")
           for name, identifier in zip(names, identifiers))
assert commands.slots() == (
    ("third_person", "keyboard", "third_person_key"),
    ("third_person", "controller", "third_person_controller"),
    ("shoulder", "keyboard", "shoulder_key"),
    ("shoulder", "controller", "shoulder_controller"),
    ("orbit", "keyboard", "orbit_key"),
    ("orbit", "controller", "orbit_controller"),
    ("zoom_in", "keyboard", "zoom_in_key"),
    ("zoom_in", "controller", "zoom_in_controller"),
    ("zoom_out", "keyboard", "zoom_out_key"),
    ("zoom_out", "controller", "zoom_out_controller"),
    ("free_look", "keyboard", "free_look_key"),
    ("free_look", "controller", "free_look_controller"),
    ("camera_distance", "keyboard", "camera_distance_key"),
    ("camera_distance", "controller", "camera_distance_controller"),
    ("sniper_zoom", "keyboard", "sniper_zoom_key"),
    ("sniper_zoom", "controller", "sniper_zoom_controller"),
)
assert commands.identifier("shoulder", "controller") == "shoulder_controller"
assert commands.defaults() == {
    "third_person_key": "P", "third_person_controller": None,
    "shoulder_key": SIX, "shoulder_controller": None,
    "orbit_key": SEVEN, "orbit_controller": None,
    "zoom_in_key": None, "zoom_in_controller": None,
    "zoom_out_key": None, "zoom_out_controller": None,
    "free_look_key": FREE_LOOK, "free_look_controller": "Gamepad_LeftThumbstick",
    "camera_distance_key": EIGHT, "camera_distance_controller": None,
    "sniper_zoom_key": FREE_LOOK, "sniper_zoom_controller": "Gamepad_LeftThumbstick",
}
assert all(bind.is_hidden is True and bind.event_filter == "IE_Pressed" for bind in commands.binds)
assert all(option.is_hidden is False for option in commands.options)
assert tuple(bind.key for bind in commands.binds) == ("P", None, SIX, None, SEVEN, None,
                                                    None, None, None, None, FREE_LOOK, "Gamepad_LeftThumbstick",
                                                    EIGHT, None, FREE_LOOK, "Gamepad_LeftThumbstick")

for bind in commands.binds:
    bind.callback()
assert calls == ["third_person", "third_person", "shoulder", "shoulder", "orbit", "orbit",
                 "zoom_in", "zoom_in", "zoom_out", "zoom_out", "camera_distance", "camera_distance"]

assert commands.validate({"shoulder_key": "ThumbMouseButton"}) == {
    "shoulder_key": "ThumbMouseButton"
}
assert commands.validate({"shoulder_controller": "Gamepad_FaceButton_Left"}) == {
    "shoulder_controller": "Gamepad_FaceButton_Left"
}
assert commands.validate({"orbit_controller": None}) == {"orbit_controller": None}

for changes in (
    {"orbit_key": SIX},
    {"zoom_in_key": "P"},
    {"zoom_in_controller": "Gamepad_FaceButton_Left",
     "zoom_out_controller": "Gamepad_FaceButton_Left"},
    {"orbit_controller": "Gamepad_FaceButton_Left",
     "shoulder_controller": "Gamepad_FaceButton_Left"},
    {"unknown": "K"},
    {"orbit_key": "Gamepad_FaceButton_Top"},
    # The sniper zoom shares a key with Free Look only (Kevin, 2026-10-09).
    {"sniper_zoom_key": "P"},
    {"sniper_zoom_key": SIX},
    {"sniper_zoom_controller": "Gamepad_FaceButton_Left", "shoulder_controller": "Gamepad_FaceButton_Left"},
    {"free_look_key": "K", "sniper_zoom_key": "K", "orbit_key": "K"},
):
    try:
        commands.validate(changes)
    except ValueError:
        pass
    else:
        raise AssertionError(changes)

assert commands.validate({"free_look_key": "K", "sniper_zoom_key": "K"}) == {"free_look_key": "K",
                                                                            "sniper_zoom_key": "K"}
assert commands.validate({"sniper_zoom_controller": "Gamepad_RightShoulder"}) == {
    "sniper_zoom_controller": "Gamepad_RightShoulder"}
commands.apply({"shoulder_controller": "Gamepad_FaceButton_Left"})
assert commands.option("shoulder_controller").value == "Gamepad_FaceButton_Left"
assert commands.option("shoulder_controller")._bind.key == "Gamepad_FaceButton_Left"
old_orbit = commands.option("orbit_key").value
commands.option("orbit_key").value = "P"
assert commands.option("orbit_key").value == old_orbit

commands.apply({"third_person_key": "Nine", "shoulder_key": "P"})
assert commands.option("third_person_key").value == "Nine"
assert commands.option("shoulder_key").value == "P"
commands.apply({"shoulder_controller": None})
assert commands.option("shoulder_controller").value is None

commands.option("orbit_controller").value = "malformed"
assert commands.option("orbit_controller").value is None
commands.align()
assert tuple(bind.key for bind in commands.binds) == ("Nine", None, "P", None, SEVEN, None,
                                                    None, None, None, None, FREE_LOOK, "Gamepad_LeftThumbstick",
                                                    EIGHT, None, FREE_LOOK, "Gamepad_LeftThumbstick")
commands.apply({"zoom_in_key": "MouseScrollUp", "zoom_out_key": "MouseScrollDown"})
assert commands.option("zoom_in_key")._bind.key == "MouseScrollUp"
commands.apply(commands.defaults())
assert commands.option("zoom_in_key")._bind.key is None

# A "Six" or "Seven" saved before the keyboard-named defaults becomes the key's name where it cannot be typed
# (Kevin's Omni Sprint, AZERTY, 2026-10-07), and stays as it is on QWERTY.
from apex_camera_runtime import camera_commands  # noqa: E402
saved = dict(camera_commands.UNREACHABLE)
camera_commands.UNREACHABLE.clear()
camera_commands.UNREACHABLE.update({"Six": "Hyphen", "Seven": "E_AccentGrave"})
commands.applying = True
commands.option("shoulder_key").value = "Six"
commands.option("orbit_key").value = "Seven"
commands.applying = False
commands.align()
assert commands.option("shoulder_key").value == "Hyphen" and commands.option("orbit_key").value == "E_AccentGrave"
assert commands.option("shoulder_key")._bind.key == "Hyphen"
assert camera_commands.normalize_camera_key("Nine") == "Nine"
camera_commands.UNREACHABLE.clear()
commands.option("shoulder_key").value = "Six"
assert commands.option("shoulder_key").value == "Six", "QWERTY keeps its Six"
camera_commands.UNREACHABLE.update(saved)
assert camera_commands.UNREACHABLE == {old: new for old, new in (("Six", SIX), ("Seven", SEVEN)) if new != old}
print("RESULTAT: OK | camera commands validate, group, align and keep callbacks")
