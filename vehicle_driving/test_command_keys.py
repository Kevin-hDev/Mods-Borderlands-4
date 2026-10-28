"""Tests the rules on the CAMERA page's keys: which option a row sets, the keys by default, and every refusal."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def status(call) -> str | None:
    try:
        call()
    except ValueError as error:
        return getattr(error, "status", "ValueError")
    return None


state = sdk_stubs.install()

from vehicle_driving import command_keys, control_config, view_key  # noqa: E402

keys = command_keys.KEYS
check("one command, the view, on the keyboard then the controller",
      control_config.SLOTS == (("view", "keyboard"), ("view", "controller"))
      and keys.options == (view_key.keyboard_key, view_key.controller_key))
check("each row names its option", keys.identifier("view", "keyboard") == "vehicle_view_key"
      and keys.identifier("view", "controller") == "vehicle_view_button")
check("a row the page does not have is refused", status(lambda: keys.identifier("zoom", "keyboard")) == "ValueError")
check("the keys by default: L, and no controller button (Kevin, 2026-10-06)",
      keys.defaults() == {"vehicle_view_key": "L", "vehicle_view_button": None})

keys.set_values({"vehicle_view_key": "K", "vehicle_view_button": "Gamepad_DPad_Up"})
check("a key saved reaches its option and its bind",
      view_key.keyboard_key.value == "K" and view_key.keyboard_bind.key == "K"
      and view_key.controller_key.value == "Gamepad_DPad_Up" and view_key.controller_bind.key == "Gamepad_DPad_Up")
check("no key is a choice too", keys.validate({"vehicle_view_button": None}) == {"vehicle_view_button": None})
check("a controller button on the keyboard's row is refused, with its own words",
      status(lambda: keys.validate({"vehicle_view_key": "Gamepad_FaceButton_Bottom"})) == "invalid_keyboard")
check("a key on the controller's row is refused, with its own words",
      status(lambda: keys.validate({"vehicle_view_button": "L"})) == "invalid_controller")
check("the left mouse button is refused: it fires the weapon",
      status(lambda: keys.validate({"vehicle_view_key": "LeftMouseButton"})) == "invalid_keyboard")
check("changes that are not a few known keys are refused",
      all(status(lambda changes=changes: keys.validate(changes)) == "ValueError"
          for changes in ({}, [], {"zoom": "K"}, {1: "K"})))
check("a refused change leaves every key as it was",
      view_key.keyboard_key.value == "K" and view_key.controller_key.value == "Gamepad_DPad_Up")

view_key.keyboard_bind.key = "J"
keys.align()
check("align gives each bind its option's key: the option is the one authority", view_key.keyboard_bind.key == "K")

console = types.SimpleNamespace(ConsoleKeys=[types.SimpleNamespace(KeyName="Tilde"),
                                             types.SimpleNamespace(KeyName="²")])
sys.modules["unrealsdk"].find_class = lambda name: types.SimpleNamespace(ClassDefaultObject=console)
check("Escape and the console's keys are refused, the one on Kevin's keyboard included",
      [keys.refusal(key) for key in ("Escape", "Tilde", "²", "K", None)]
      == ["reserved_key", "reserved_key", "reserved_key", None, None])


def unreadable(name: str) -> None:
    raise RuntimeError("no InputSettings")


sys.modules["unrealsdk"].find_class = unreadable
check("a key whose clash with the console cannot be checked is not saved, and said once",
      keys.refusal("K") == "failed" and any("console shortcuts unavailable" in line for line in state["errors"]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
