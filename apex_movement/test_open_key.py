"""F10 opens Apex Movement's window in game (Kevin, 2026-10-18), in the full pack only: its key and its option belong
to the mod, the window's COMMANDS page finds them, the key's press opens the window, and a separate movement file
carries none of it. The card and its rules are the camera windows' shared code, tested in Third Person & FOV's real
window (its test_open_key.py)."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True
opened = []
fake_window = types.ModuleType("apex_movement.control_window")
fake_window.start = lambda: opened.append("window")
sys.modules["apex_movement.control_window"] = fake_window

import apex_movement  # noqa: E402
from apex_movement import camera_control_config, camera_settings, movements, pack  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


key = camera_settings.open_key
mod = apex_movement.mod
check("F10 at first, saved with the mod's settings, its keybind the mod's",
      key.default == "F10" and key.chosen() == "F10" and key.bind.key == "F10"
      and key.option in mod.kwargs["options"] and key.bind in mod.kwargs["keybinds"])
check("the window's COMMANDS page finds it", camera_control_config.OPEN_KEY is key)
key.bind.callback()
check("its press opens the window", opened == ["window"])
key.option.value = "F8"
check("another key chosen: the keybind follows", key.align() and key.bind.key == "F8" and not key.align())
key.option.value = 42
check("a value the file holds that is no key: F10", key.key() == "F10")
key.option.value = "F10"
key.align()
check("in the full pack only: a separate movement file carries neither the key nor its card",
      {"open_key", "panel_open_key"} <= set(movements.FULL_ONLY))
saved = pack.CARRIES
pack.CARRIES = ("Slide",)
check("the separate file's check says so", not pack.carries_module("open_key")
      and not pack.carries_module("panel_open_key"))
pack.CARRIES = saved

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
