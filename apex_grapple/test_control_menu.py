"""One entry opens the native window; the real previous settings still round-trip."""

import json
import shutil
import tempfile
import types
from pathlib import Path

import control_fixture as f
from apex_grapple import control_window, menu, settings_moved

visible = [option for option in menu.MENU if not option.is_hidden]
assert visible[5] is f.control_menu.MENU
assert not hasattr(visible[5], "children")
opened = []
control_window.start = lambda **kwargs: opened.append(kwargs)
visible[5].on_press(visible[5])
assert opened == [{"return_to_menu": True}]
assert f.control_menu.STORAGE.is_hidden


def load(options, values):
    for option in options:
        if option.identifier not in values:
            continue
        if hasattr(option, "children"):
            load(option.children, values[option.identifier])
        elif hasattr(option, "value"):
            option.value = values[option.identifier]


def snapshot(options):
    result = {}
    for option in options:
        if hasattr(option, "children"):
            result[option.identifier] = snapshot(option.children)
        elif hasattr(option, "value"):
            result[option.identifier] = option.value
    return result


saved = json.loads((Path(__file__).parent / "fixtures/control_settings_0_12_0.json").read_text())
load(f.mod.options, saved["options"])
# The rope's switch moved to the look's line after 1.0.9: the mod takes it from its former line (settings_moved.py).
folder = Path(tempfile.mkdtemp())
try:
    (folder / "settings.json").write_text(json.dumps(saved), encoding="utf-8")
    assert settings_moved.adopt(types.SimpleNamespace(settings_file=folder / "settings.json"), menu.MOVED) == [
        "show_rope"]
finally:
    shutil.rmtree(folder)
current = snapshot(f.mod.options)
assert current.pop("menu_language") == "EN", "Older settings gain English without a migration"
assert current.pop("controller_icons") == "PS5", "Older settings gain Kevin's chosen icon default"
assert current.pop("menu_last_page") == "shot", "Older settings start on the first tab without a migration"
assert current.pop("menu_theme") == "EMBER", "Older settings keep the menus' first theme without a migration"
assert current.pop("menu_window_size") == "LARGE", "Older settings open in the new default size, LARGE"
assert current.pop("menu_last_scroll") == 0, "Older settings open at the top of the page"
assert current["shot_menu"].pop("stamina_cost") == 33, "Older settings gain the reserve cost at its default"
assert current.pop("hold_menu") == {"keyboard_hold": False, "controller_hold": False, "hold_time": 0.4},     "Older settings gain the hold mode, off"
assert current.pop("look_menu") == {
    "show_rope": saved["options"]["shot_menu"].pop("show_rope"), "look": "GRAPPLE_GUN", "rope_look": "A",
    "rope_thickness": "L", "rope_light": "2", "rope_movement": "H", "hook_size": "B", "holster": "WITH",
    "glow_face": "D", "rope_colour": "ORANGE", "game_rope_colour": "BLUE"}, \
    "Older settings keep the rope's switch on the look's line and gain the look at its first"
assert current == saved["options"], "Existing controls and gameplay settings must survive"
for device, stored in zip(f.config.DEVICES, f.control_menu.STORAGE.children):
    assert stored.identifier == f"{device.name}_controls" and stored.is_hidden
    assert all(option.is_hidden and option.mod is f.mod for option in stored.children)
assert not any(option.identifier.endswith(("_single", "_double", "_default")) for option in visible)
print("OK | direct window entry, hidden storage, previous real settings round-trip, no legacy menus")
