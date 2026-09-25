"""The custom window edits only this pack's existing SDK options."""

from movement_test_result import Reporter

result = Reporter("Movement panel saves existing options, validates and restores without changing gameplay")

import math
import sys

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import pack, settings, walk_key
from apex_movement import panel_model, panel_preferences, panel_theme


class Mod:
    def __init__(self):
        self.is_enabled = True
        self.fail = False
        self.saved = 0

    def save_settings(self):
        if self.fail:
            raise OSError("private path")
        self.saved += 1

    def enable(self):
        self.is_enabled = True

    def disable(self):
        self.is_enabled = False


mod = Mod()
model = panel_model.Model(mod)
assert len(model.groups) == len(model.pages) == 10
assert model.pages == panel_theme.PAGES
assert tuple(model.camera_options) == ("third_person", "third_person_key", "custom_fov", "fov")
# 30 movement settings, the walk key's three (switch, key, speed) and the four camera rows.
assert len(model.options) == 37
assert [key for key in model.options if key.startswith("walk")] == ["walk_speed", "walk", "walk_key", "walk_key_speed"]
assert "native_fov" not in model.options and "applied_fov" not in model.options
assert model.language == "EN" and model.page == model.pages[0]
assert panel_preferences.french.default_value is False
assert panel_preferences.PAGE_KEYS[-1] == "options"
assert model.change_language("FR") and model.language == "FR"
assert not model.change_language("other")
assert model.change_page("dash") and model.page == "dash"
assert model.change_page("options") and model.page == "options"
panel_preferences.last_page.value = float(panel_preferences.PAGE_KEYS.index("glide"))
assert model.page == "glide"  # A JSON number can load as float without losing the saved page.
panel_preferences.last_page.value = float("nan")
assert model.page == model.pages[0]
panel_preferences.last_page.value = panel_preferences.PAGE_KEYS.index("dash")
assert not model.change_page("missing")
before = settings.dash_distance.value
assert model.write({"dash_distance": 222}) and settings.dash_distance.value == 220
for bad in ({"unknown": 1}, {"dash": 1}, {"dash_distance": float("nan")},
            {"dash_distance": float("inf")}, {"dash_distance": 2000}):
    assert not model.write(bad)
assert math.isclose(settings.dash_distance.value, 220)
assert model.write({"third_person_key": "K"})
assert model.camera_options["third_person_key"].value == "K"
assert not model.write({"third_person_key": "Gamepad_FaceButton_Top"})
assert model.camera_options["third_person_key"].value == "K"
assert model.write({"walk_key": "LeftAlt"}) and walk_key.bind.key == "LeftAlt"
assert not model.write({"walk_key": "LeftMouseButton"}) and walk_key.key.value == "LeftAlt"
# A separate Apex Auto Sprint file ships no camera_settings: the key it captures must be checked without it.
pack.CARRIES = ("Auto sprint",)
sys.modules["apex_movement.camera_settings"] = None
try:
    alone = panel_model.Model(mod)
    assert not alone.camera_options
    assert alone.write({"walk_key": "CapsLock"}) and walk_key.bind.key == "CapsLock"
finally:
    del sys.modules["apex_movement.camera_settings"]
    pack.CARRIES = ()
mod.fail = True
assert not model.write({"dash_distance": 240})
assert settings.dash_distance.value == 220
mod.fail = False
assert model.restore() and settings.dash_distance.value == before
assert model.can_undo
assert model.undo() and settings.dash_distance.value == 220
assert not model.can_undo
assert model.toggle_enabled() and not mod.is_enabled
assert model.write({"dash_distance": 230}) and not mod.is_enabled
assert model.toggle_enabled() and mod.is_enabled
result.success()
