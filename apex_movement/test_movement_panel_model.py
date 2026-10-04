"""The custom window edits only this pack's existing SDK options."""

from movement_test_result import Reporter

result = Reporter("Movement panel saves existing options, validates and restores without changing gameplay")

import math
import sys

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import camera, camera_settings, pack, settings, walk_key
from apex_movement import panel_en, panel_fr, panel_model, panel_preferences, panel_theme, report


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
assert not ({option.identifier for option in camera_settings.VISIBLE}
            & {option.identifier for option in camera_settings.commands.options})
assert len(model.groups) == 10 and len(model.pages) == 11
assert model.pages == panel_theme.PAGES
assert model.pages[-1] == "commands"
assert tuple(model.camera_options) == ("third_person", "third_person_ads", "shoulder_left", "orbit", "custom_fov", "fov", "extended_loot", "loot_reach")
assert tuple(model.command_options) == (
    "third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
    "orbit_key", "orbit_controller", "zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller")
# Movement, walk and eight camera/loot choices; commands have their own page.
assert len(model.options) == 42
assert ([key for key in model.options if key.startswith("walk")]
        == ["walk_speed", "walk", "walk_key", "walk_toggle", "walk_key_speed"])
assert "native_fov" not in model.options and "applied_fov" not in model.options
assert model.language == "EN" and model.page == model.pages[0]
assert model.controller_icons == "PS5"
assert model.change_controller_icons("XSX") and model.controller_icons == "XSX"
assert not model.change_controller_icons("other")
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
assert model.write_commands({"third_person_key": "K"})
assert model.command_options["third_person_key"].value == "K"
assert model.write_commands({"shoulder_key": "ThumbMouseButton"})
assert model.command_options["shoulder_key"].value == "ThumbMouseButton"
assert not model.write_commands({"orbit_key": "Escape"})
assert not model.write_commands({"third_person_key": "Gamepad_FaceButton_Top"})
assert model.command_options["third_person_key"].value == "K"
assert model.write({"walk_key": "LeftAlt"}) and walk_key.bind.key == "LeftAlt"
assert not model.write({"walk_key": "LeftMouseButton"}) and walk_key.key.value == "LeftAlt"

# Live camera rows route through the elected runtime. Orbit stays at its committed value until
# the frame loop confirms the requested mode; Restore and Undo use the same route.
camera_settings.shoulder_left.mod.is_enabled = True
camera_calls = []
orbit_deferred = [False]
orbit_refused = [False]
shoulder_refused = [False]
camera_ready = [True]


def set_shoulder(left):
    camera_calls.append(("shoulder", left))
    if shoulder_refused[0]:
        return False
    camera_settings.set_shoulder_left(left)
    return True


def set_orbit(enabled):
    camera_calls.append(("orbit", enabled))
    if orbit_refused[0]:
        return False
    if not orbit_deferred[0]:
        camera_settings.set_orbit(enabled)
    return True


camera.set_shoulder, camera.set_orbit = set_shoulder, set_orbit
camera.ready = lambda: camera_ready[0]
assert model.write({"shoulder_left": True})
assert camera_calls[-1] == ("shoulder", True) and camera_settings.shoulder_left.value is True
orbit_deferred[0] = True
assert model.write({"orbit": True}) is None
assert camera_calls[-1] == ("orbit", True) and camera_settings.orbit.value is False
camera_settings.set_orbit(True)
assert model.advance() == "saved"
camera_settings.third_person.value = True
assert model.restore() is None
assert (camera_calls[-1] == ("orbit", False) and camera_settings.orbit.value is True
        and camera_settings.shoulder_left.value is True and camera_settings.third_person.value is True
        and not model.can_undo)
pending_key = camera_settings.third_person_key.value
assert not model.assign_command("third_person", "keyboard", "L")
assert not model.write_commands({"third_person_key": "L"})
assert not model.default_commands() and camera_settings.third_person_key.value == pending_key
camera_settings.set_orbit(False)
assert model.advance() == "restored"
assert (camera_settings.shoulder_left.value is False
        and camera_settings.third_person.value is False and model.can_undo
        and camera_settings.third_person_key.value == "P")
camera_ready[0] = False
calls_before_undo = len(camera_calls)
assert model.undo() is None
assert not model.assign_command("third_person", "keyboard", "L")
assert not model.default_commands() and camera_settings.third_person_key.value == "P"
assert model.advance() is None
assert len(camera_calls) == calls_before_undo
camera_ready[0] = True
assert model.advance() is None
camera_settings.set_orbit(True)
assert model.advance() == "undone"
assert (camera_settings.orbit.value is True and camera_settings.shoulder_left.value is True
        and camera_settings.third_person.value is True and not model.can_undo
        and camera_settings.third_person_key.value == "K")
orbit_refused[0] = True
camera_settings.set_orbit(False)
assert not model.write({"orbit": True, "dash_distance": 240})
assert camera_settings.orbit.value is False and settings.dash_distance.value == 220
orbit_refused[0] = False
camera_settings.set_orbit(True)
shoulder_refused[0] = True
assert model.restore() is None
camera_settings.set_orbit(False)
assert model.advance() is None  # Shoulder refusal starts an asynchronous Orbit compensation.
camera_settings.set_orbit(True)
assert model.advance() == "failed"
assert (camera_settings.orbit.value is True and camera_settings.shoulder_left.value is True
        and camera_settings.third_person.value is True and not model.can_undo)
shoulder_refused[0] = False
orbit_deferred[0] = False
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
# If the command half of a global Restore fails, the already-saved settings half is compensated.
settings.dash.value = False
assert model.write_commands({"third_person_key": "K"})
apply_commands = model.command_actions.apply
model.command_actions.apply = lambda _values: False
assert not model.restore()
assert settings.dash.value is False and camera_settings.third_person_key.value == "K" and not model.can_undo
model.command_actions.apply = apply_commands
assert model.toggle_enabled() and not mod.is_enabled
assert model.write({"dash_distance": 230}) and not mod.is_enabled
assert model.toggle_enabled() and mod.is_enabled


# A switch that does not take keeps the state, writes its cause in the log and names the line the window shows.
class Outdated(RuntimeError):
    notice = "camera_outdated"


def refuse():
    raise Outdated("incompatible shared camera state")


errors = []
report.logging.error = errors.append
report.reset()
mod.is_enabled = False
mod.enable = refuse
assert model.toggle_enabled() is False and not mod.is_enabled
assert model.toggle_notice == "camera_outdated"
assert errors == ["[Apex Movement] could not switch the mod on: Outdated: incompatible shared camera state"]
mod.enable = lambda: (_ for _ in ()).throw(OSError("private path"))
assert model.toggle_enabled() is False and model.toggle_notice == "toggle_failed" and len(errors) == 2
del mod.enable
assert model.toggle_enabled() and mod.is_enabled
assert all("camera_outdated" in text and "toggle_failed" in text for text in (panel_en.TEXT, panel_fr.TEXT))
camera_settings.zoom.option.value = 600
assert model.default_commands() and camera_settings.zoom.distance() == 600
assert model.restore() and camera_settings.zoom.distance() == 300
assert model.undo() and camera_settings.zoom.distance() == 600
result.success()
