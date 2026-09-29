"""Tests the devices the CONTROLS page reads: the keyboard's key and the controller's button, one each."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import control_config as config, keys  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


keyboard, gamepad = config.DEVICES
check("two devices, named as Grapple's page words them", (keyboard.name, gamepad.name) == ("keyboard", "gamepad"))
check("each device is one of the two keys' options", keyboard.option is keys.keyboard_key
      and gamepad.option is keys.controller_key and config.ALL == (keys.keyboard_key, keys.controller_key))
check("a controller button belongs to the controller, anything else to the keyboard",
      config.device_of("Gamepad_FaceButton_Left") == "gamepad" and config.device_of("A") == "keyboard"
      and config.device_of("ThumbMouseButton") == "keyboard")
check("a device's selection is its one key", gamepad.selection() == ("Gamepad_FaceButton_Left",))
keys.keyboard_key.value = None
check("an unbound key selects nothing", keyboard.selection() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
