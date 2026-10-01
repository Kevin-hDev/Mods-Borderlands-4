"""Tests the two inspection keys: hidden binds shown once each through their option, with no key by default on either
device, each device refusing the other's; silent until the heirloom runs, then a press or a mouse double click asks
the heirloom for its inspection, a release or a key held never does; never blocking the game, an error said once per
key and never raised; the heirloom's start gives each bind its option's key, and lets a failure be said again."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fake_player  # noqa: E402
import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()

from apex_heirloom import heirloom, inspect_keys, lifecycle  # noqa: E402

asked: list[int] = []
heirloom.inspect = lambda: asked.append(1)
keyboard, controller = inspect_keys.keyboard_bind, inspect_keys.controller_bind


def press(bind, name: str = "IE_Pressed"):
    """What the key's callback gives the SDK, or what it raised: a failure of its check, not of the whole test."""
    try:
        return bind.callback(fake_player.event(name))
    except Exception as error:
        return error


check("each bind is hidden and shown once, through its option",
      keyboard.is_hidden and controller.is_hidden and inspect_keys.keyboard_key.is_hidden is False
      and inspect_keys.controller_key.is_hidden is False)
check("no key by default, neither keyboard nor controller (Kevin, 2026-09-30)",
      keyboard.key is None and controller.key is None and keyboard.default_key is None
      and controller.default_key is None and inspect_keys.keyboard_key.value is None
      and inspect_keys.controller_key.value is None)
check("saved under their own names, apart from the put-away keys",
      (keyboard.identifier, controller.identifier) == ("inspect_keyboard", "inspect_controller"))
check("each entry of the SDK's menu names its device and the inspection",
      keyboard.display_name == "Keyboard: Inspect" and controller.display_name == "Controller: Inspect")
check("each is read on every event, so that a mouse double click counts",
      keyboard.event_filter is None and controller.event_filter is None)
inspect_keys.keyboard_key.value = "F"
inspect_keys.controller_key.value = "Gamepad_DPad_Up"
check("a key chosen in the menu reaches its bind", keyboard.key == "F" and controller.key == "Gamepad_DPad_Up")
inspect_keys.keyboard_key.value = "Gamepad_FaceButton_Left"
inspect_keys.controller_key.value = "F"
check("a controller button is refused on the keyboard's option, a key on the controller's, each then unbound",
      inspect_keys.keyboard_key.value is None and inspect_keys.controller_key.value is None
      and keyboard.key is None and controller.key is None)
inspect_keys.keyboard_key.value = "LeftMouseButton"
check("the left mouse button, which fires, is refused", inspect_keys.keyboard_key.value is None)
inspect_keys.keyboard_key.value = "MouseScrollUp"
check("the wheel, which changes weapon and would cut the inspection, is refused (2026-09-30)",
      inspect_keys.keyboard_key.value is None and keyboard.key is None)
inspect_keys.keyboard_key.value, inspect_keys.controller_key.value = "F", "Gamepad_DPad_Up"

lifecycle.STATE.running = False
check("before the heirloom runs, a press does nothing and never blocks the game",
      press(keyboard) is None and press(controller) is None and asked == [])
lifecycle.STATE.running = True
check("the heirloom running, a press asks for the inspection, without blocking the game",
      press(keyboard) is None and asked == [1])
press(keyboard, "IE_Released")
press(keyboard, "IE_Repeat")
check("a release or a key held asks nothing more: one gesture per press", asked == [1])
press(keyboard, "IE_DoubleClick")
check("a mouse button pressed twice quickly comes as a double click: the second press counts", asked == [1, 1])
press(controller)
check("the controller's button asks too", len(asked) == 3)


def broken() -> None:
    raise RuntimeError("arms gone")


heirloom.inspect = broken
errors = len(state["errors"])
check("an error never reaches the game's key handling", press(keyboard) is None and press(keyboard) is None)
check("it is written once per key in the log, with its reason", len(state["errors"]) == errors + 1
      and "keyboard inspection key not followed" in state["errors"][-1] and "arms gone" in state["errors"][-1])
press(controller)
check("the other key's is said on its own", len(state["errors"]) == errors + 2
      and "controller inspection key" in state["errors"][-1])

# As mods_base loads a settings file edited by hand: its own copy of the keys, after the options, unchecked.
keyboard.key, controller.key = "LeftMouseButton", "Gamepad_LeftX"
inspect_keys.start()
check("the heirloom's start gives each bind its option's key",
      keyboard.key == "F" and controller.key == "Gamepad_DPad_Up")
press(keyboard)
check("after a new start, a failure is said again", len(state["errors"]) == errors + 3)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
