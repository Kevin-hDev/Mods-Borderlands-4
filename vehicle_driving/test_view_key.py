"""Tests the view key: a setting per device, its bind following it; at the wheel the next view, saved; nothing on
foot; never an error into the game's input."""

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


def busy() -> None:
    raise RuntimeError("Settings save already in progress")


def lost(**kwargs: object) -> None:
    raise RuntimeError("no controller")


state = sdk_stubs.install()

import vehicle_driving  # noqa: E402
from vehicle_driving import settings, view_key  # noqa: E402

keyboard, controller = view_key.keyboard_bind, view_key.controller_bind
check("a keyboard key, L by default (Kevin, 2026-10-06), and a controller button left free",
      (keyboard.identifier, keyboard.key, controller.identifier, controller.key)
      == ("vehicle_view_key", "L", "vehicle_view_button", None))
check("both binds hidden, each key shown once, by its option: a bind listed under Keybinds too would not reach it",
      keyboard.is_hidden and controller.is_hidden and view_key.BINDS == [keyboard, controller]
      and [(option.identifier, option.value, option.default_value, option.is_hidden) for option in view_key.OPTIONS]
      == [("vehicle_view_key", "L", "L", False), ("vehicle_view_button", None, None, False)])
check("both fire once a press, mods_base's default", all("event_filter" not in bind.kwargs for bind in view_key.BINDS))
view_key.keyboard_key.value = "K"
check("a key set on its option reaches its bind", keyboard.key == "K")
view_key.keyboard_key.value = "Gamepad_FaceButton_Top"
check("a controller button loaded for the keyboard unbinds it", view_key.keyboard_key.value is None and keyboard.key is None)
view_key.keyboard_key.value = "L"

state["pc"] = types.SimpleNamespace(Pawn=types.SimpleNamespace(Name="OakCharacter_1"))
saves = state.get("saves", 0)
check("on foot a press changes nothing", keyboard.callback() is None and settings.vehicle_view.value == "Default"
      and state.get("saves", 0) == saves)
state["pc"] = types.SimpleNamespace(Pawn=sdk_stubs.Vehicle("OakVehicle_1"))
seen: list[str] = []
results: list[object] = []
for _ in settings.VIEWS:
    results.append(keyboard.callback())
    seen.append(settings.vehicle_view.value)
check("at the wheel each press goes to the next view, the mod's settings saved each time, and lets the key through",
      seen == ["Close", "Closer", "Closest", "Custom", "Far", "Default"] and state["saves"] == saves + 6
      and results == [None] * 6)
controller.callback()
check("the controller button does the same", settings.vehicle_view.value == "Close" and state["saves"] == saves + 7)
check("a save that fails keeps the view and is reported; nothing reaches the game's input",
      view_key.press(busy) is None and settings.vehicle_view.value == "Closer"
      and any("camera view could not be saved" in line for line in state["errors"]))
view_key.get_pc = lost
check("a controller that cannot be read: nothing changes, it is reported, nothing reaches the game's input",
      keyboard.callback() is None and settings.vehicle_view.value == "Closer"
      and any("the view key failed" in line for line in state["errors"]))
check("the mod the key saves is the one built", vehicle_driving.mod is state["mods"][0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
