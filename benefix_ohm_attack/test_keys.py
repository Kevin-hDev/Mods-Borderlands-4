"""Tests the beam's two keys: none bound by default, each held or not from its own events, either one firing, and each
bind taking its option's key."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import control_config, keys  # noqa: E402
from benefix_ohm_attack.command_keys import KEYS  # noqa: E402

fails: list[str] = []
PRESSED, RELEASED, DOUBLE = "EInputEvent.IE_Pressed", "EInputEvent.IE_Released", "EInputEvent.IE_DoubleClick"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


binds = (keys.keyboard_bind, keys.controller_bind)
check("no key is bound until the player chooses one, on either device",
      all(bind.key is None and bind.default_key is None for bind in binds)
      and keys.keyboard_key.value is None and keys.controller_key.value is None)
check("both press and release are listened to, and each bind is hidden: its option is its one entry in the SDK's menu",
      all(bind.event_filter is None and bind.is_hidden for bind in binds)
      and not keys.keyboard_key.is_hidden and not keys.controller_key.is_hidden)
check("each entry names its device", keys.keyboard_bind.display_name.startswith("Keyboard:")
      and keys.controller_bind.display_name.startswith("Controller:")
      and keys.keyboard_key.identifier == "fire_keyboard" and keys.controller_key.identifier == "fire_controller")
check("the COMMANDS page has one command, FIRE, on the two devices, with these options and binds",
      [command.name for command in control_config.COMMANDS] == ["fire"]
      and control_config.SLOTS == (("fire", "keyboard"), ("fire", "controller"))
      and control_config.ALL == (keys.keyboard_key, keys.controller_key)
      and control_config.COMMANDS[0].binds == binds and KEYS.options == control_config.ALL)

check("nothing is held at first", not keys.held())
keys.keyboard_bind.callback(PRESSED)
check("the keyboard's key pressed is held", keys.held())
keys.keyboard_bind.callback("EInputEvent.IE_Repeat")
check("a repeat changes nothing", keys.held())
keys.keyboard_bind.callback(RELEASED)
check("released, it no longer is", not keys.held())
keys.keyboard_bind.callback(DOUBLE)
check("a mouse double click holds as a press does", keys.held())
keys.keyboard_bind.callback(RELEASED)
keys.controller_bind.callback(PRESSED)
check("the controller's button fires as well", keys.held())
keys.keyboard_bind.callback(PRESSED)
keys.controller_bind.callback(RELEASED)
check("with both down, one released still fires", keys.held())
keys.keyboard_bind.callback(RELEASED)
check("both released, nothing fires", not keys.held())
keys.controller_bind.callback(PRESSED)
keys.release()
check("a key still down is forgotten when asked: a menu never sees its release", not keys.held())

keys.keyboard_key.value, keys.controller_key.value = "N", "Gamepad_LeftShoulder"
keys.keyboard_bind.key = keys.controller_bind.key = "Stale"
keys.keyboard_bind.callback(PRESSED)
keys.align()
check("aligning gives each bind its option's key, and forgets what was held",
      keys.keyboard_bind.key == "N" and keys.controller_bind.key == "Gamepad_LeftShoulder" and not keys.held())

for value, label in (("MouseScrollUp", "the wheel"), ("Gamepad_FaceButton_Top", "a controller button"),
                     ("LeftMouseButton", "the left mouse button"), (12, "what is not a name")):
    keys.keyboard_key.value = value
    check(f"{label} given to the keyboard's option leaves it unbound", keys.keyboard_key.value is None)
keys.controller_key.value = "N"
check("a keyboard key given to the controller's option leaves it unbound", keys.controller_key.value is None)
keys.keyboard_key.value = "ThumbMouseButton"
check("a mouse side button is a key as another", keys.keyboard_key.value == "ThumbMouseButton")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
