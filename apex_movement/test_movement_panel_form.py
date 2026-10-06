"""A click is never missed, and failed saves keep the Movement menu open."""

from movement_test_result import Reporter

result = Reporter("Movement menu latches clicks, saves pages and keeps a failed close open")

from types import SimpleNamespace

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import camera, camera_settings, panel_camera_commands, panel_form, panel_labels, panel_model
from apex_movement import panel_theme, settings


from movement_ui_fixture import Widget


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


panel_labels.apply = lambda *_: None
panel_camera_commands.refresh = lambda *_: None
shown = {}  # What the labels would show beside each setting: for the shortcut, the key in its key field.
panel_labels.value = lambda _widgets, option, current, _language: shown.__setitem__(option.identifier, current)
mod = Mod()
model = panel_model.Model(mod)
names = ["focus", "pages", "notice", "close", "theme", "window_size", "options", "language:EN", "language:FR",
         "restore", "undo", "enabled", "row:fov", "description:fov",
         "row:walk_toggle", "description:walk_toggle", "row:walk_key_speed", "description:walk_key_speed",
         "row:loot_reach", "description:loot_reach", "row:shoulder_left", "description:shoulder_left",
         "row:orbit", "description:orbit", "row:third_person_ads", "description:third_person_ads"]
names += [f"nav:{page}" for page in model.pages]
names += [f"setting:{key}" for key in model.options]
names += [f"{part}:{key}" for key in ('shoulder_smooth', 'orbit_smooth', 'shoulder_seconds') for part in ('row', 'description')]
for action in ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out"):
    names += [f"heading:command_{action}", f"group:command_{action}"]
    for device in ("keyboard", "controller"):
        base = f"{action}:{device}"
        names += [f"device:{base}", f"command:{base}", f"clear:{base}", f"clear:{base}_label",
                  f"value:{base}", f"value:{base}:icon"]
names += ["heading:command_tools", "group:command_tools", "commands_reset", "commands_reset_label",
          "commands_status", "icons_label", "icons:PS5", "icons:PS5_label", "icons:XSX", "icons:XSX_label"]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
assert widgets["setting:fov"].enabled is False
assert widgets["row:fov"].opacity < 1 and widgets["description:fov"].opacity < 1
# The walk key is on by default: its toggle and its speed are live.
assert widgets["setting:walk_key_speed"].enabled is True and widgets["row:walk_key_speed"].opacity == 1.0
assert widgets["setting:walk_toggle"].enabled is True and widgets["row:walk_toggle"].opacity == 1.0
widgets["setting:walk"].checked = True
assert not form.poll() and form.pending["walk"] is False
assert widgets["setting:walk_key_speed"].enabled is False and widgets["row:walk_key_speed"].opacity < 1
assert widgets["setting:walk_toggle"].enabled is False and widgets["row:walk_toggle"].opacity < 1
widgets["setting:walk"].checked = True
assert not form.poll() and "walk" not in form.pending and widgets["row:walk_key_speed"].opacity == 1.0
assert widgets["row:walk_toggle"].opacity == 1.0
# Orbit is independent of third person; the shoulder still requires it (Kevin, 2026-10-06).
assert widgets["setting:loot_reach"].enabled is True and widgets["row:loot_reach"].opacity == 1.0
for name in ("shoulder_left",):
    assert widgets[f"setting:{name}"].enabled is False and widgets[f"row:{name}"].opacity < 1
    assert widgets[f"description:{name}"].opacity < 1
assert widgets['setting:orbit'].enabled is True and widgets['row:orbit'].opacity == 1.0
widgets["setting:extended_loot"].checked = True
assert not form.poll() and form.pending["extended_loot"] is False
assert widgets["setting:loot_reach"].enabled is False and widgets["row:loot_reach"].opacity < 1
widgets["setting:extended_loot"].checked = True
assert not form.poll() and "extended_loot" not in form.pending and widgets["setting:loot_reach"].enabled is True
widgets["setting:third_person"].checked = True
assert not form.poll() and form.pending["third_person"] is True
assert all(widgets[f"setting:{name}"].enabled is True and widgets[f"row:{name}"].opacity == 1.0
           for name in ("shoulder_left", "orbit"))
widgets["setting:third_person"].checked = True
assert not form.poll() and "third_person" not in form.pending and widgets["setting:orbit"].enabled is True

widgets["options"].checked = True
assert not form.poll() and widgets["pages"].active == len(model.pages)
assert form.options_open
assert model.page == "options"
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
assert form.options_open and widgets["pages"].active == len(model.pages)
widgets["setting:custom_fov"].checked = True
assert not form.poll() and widgets["setting:fov"].enabled is True
assert widgets["row:fov"].opacity == 1.0 and widgets["description:fov"].opacity == 1.0
form.changed_at -= panel_theme.SAVE_DELAY_NS
assert not form.poll()
assert form.options_open and widgets["pages"].active == len(model.pages)
widgets["setting:fov"].value = 125
assert not form.poll()
form.changed_at -= panel_theme.SAVE_DELAY_NS
assert not form.poll()
assert form.options_open and widgets["pages"].active == len(model.pages)

widgets["setting:dash"].checked = True
assert not form.poll() and form.pending == {"dash": False}
widgets["nav:glide"].checked = True
assert not form.poll() and settings.dash.value is False and model.page == "glide"
assert widgets["pages"].active == model.pages.index("glide")
assert not form.options_open
widgets["options"].checked = True
form.poll()
widgets["language:FR"].checked = True
assert not form.poll() and model.language == "FR"

deferred = [True]
camera_ready = [True]


def set_shoulder(left):
    camera_settings.set_shoulder_left(left)
    return True


def set_orbit(enabled):
    if not deferred[0]:
        camera_settings.set_orbit(enabled)
    return True


camera.set_shoulder, camera.set_orbit = set_shoulder, set_orbit
camera.ready = lambda: camera_ready[0]
camera_settings.shoulder_left.mod.is_enabled = True
camera_settings.third_person.value = True
camera_settings.set_shoulder_left(True)
camera_settings.set_orbit(True)
form.sync(widgets)
widgets["restore"].checked = True
assert not form.poll() and form.notice == "ready" and model.transaction.pending
assert camera_settings.orbit.value is True and camera_settings.shoulder_left.value is True
camera_settings.set_orbit(False)
assert not form.poll() and form.notice == "restored" and not model.transaction.pending
assert (not camera_settings.third_person.value and not camera_settings.shoulder_left.value
        and not camera_settings.orbit.value and model.can_undo)
widgets["undo"].checked = True
camera_ready[0] = False
assert not form.poll() and form.notice == "ready" and model.transaction.pending
widgets["close"].checked = True
assert not form.poll() and model.transaction.pending
assert not form.poll() and form.notice == "ready" and model.transaction.pending
camera_ready[0] = True
assert not form.poll() and form.notice == "ready" and model.transaction.pending
camera_settings.set_orbit(True)
assert not form.poll() and form.notice == "undone" and not model.transaction.pending
assert (camera_settings.third_person.value and camera_settings.shoulder_left.value
        and camera_settings.orbit.value and not model.can_undo)
deferred[0] = False

widgets["restore"].checked = True
assert not form.poll() and settings.dash.value is True and model.can_undo
widgets["undo"].checked = True
assert not form.poll() and settings.dash.value is False and not model.can_undo


# A switch that does not take is not a failed save: the window shows the line the error names, or the switch's own.
class Outdated(RuntimeError):
    notice = "camera_outdated"


def refuse():
    raise Outdated("incompatible shared camera state")


mod.is_enabled = False
mod.enable = refuse
widgets["enabled"].checked = True
assert not form.poll() and form.notice == "camera_outdated" and not mod.is_enabled
mod.enable = lambda: (_ for _ in ()).throw(OSError("private path"))
widgets["enabled"].checked = True
assert not form.poll() and form.notice == "toggle_failed" and not mod.is_enabled
del mod.enable
widgets["enabled"].checked = True
assert not form.poll() and form.notice == "saved" and mod.is_enabled

mod.fail = True
widgets["setting:dash_distance"].value = 230
widgets["close"].checked = True
assert not form.poll() and settings.dash_distance.value == 200
mod.fail = False
assert model.transaction.pending
model.transaction.clock = lambda: model.transaction.retry_after + 1
assert not form.poll() and not model.transaction.pending
widgets["close"].checked = True
assert form.poll()

# Escape closes as the Close button does (control_escape): a failed save keeps the window open, and the change still
# pending is saved before it closes.
mod.fail = True
widgets["setting:dash_distance"].value = 230
assert not form.poll() and form.pending == {"dash_distance": 230}
assert not form.escape() and settings.dash_distance.value == 200
mod.fail = False
model.transaction.clock = lambda: model.transaction.retry_after + 1
assert not form.poll() and not model.transaction.pending
widgets["setting:dash_distance"].value = 240
assert not form.poll() and form.pending == {"dash_distance": 240}
assert form.escape() and settings.dash_distance.value == 240 and not form.pending
result.success()
