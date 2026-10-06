"""Omni Sprint's window reads each click once: the shortcut's capture, the FOV row's grey, languages and saves."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from omni_sprint import camera_control_config, panel_camera_commands, panel_camera_pages, panel_form  # noqa: E402
from omni_sprint import panel_ownership  # noqa: E402
from omni_sprint import panel_labels, panel_model, panel_theme, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Widget:
    def __init__(self):
        self.checked = False
        self.value = 0.0
        self.active = 0
        self.enabled = True
        self.opacity = 1.0
        self.selecting = False
        self.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="None"))

    def IsChecked(self):
        return self.checked

    def SetIsChecked(self, value):
        self.checked = value

    def SetValue(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def SetActiveWidgetIndex(self, value):
        self.active = value

    def SetIsEnabled(self, value):
        self.enabled = value

    def SetRenderOpacity(self, value):
        self.opacity = value

    def SetVisibility(self, value):
        self.visibility = value

    def SetText(self, value):
        self.text = value

    def SetSelectedKey(self, value):
        self.SelectedKey = value

    def GetIsSelectingKey(self):
        return self.selecting


class Mod:
    def __init__(self):
        self.is_enabled = True
        self.fail = False

    def save_settings(self):
        if self.fail:
            raise OSError("private path")

    def enable(self):
        self.is_enabled = True

    def disable(self):
        self.is_enabled = False


panel_labels.apply = lambda *_: None
panel_camera_commands.refresh = lambda *_: None
panel_ownership.w.enum = lambda name, member: f"{name}.{member}"
shown = {}  # What the labels would show beside each setting: for the shortcut, the key in its key field.
panel_labels.value = lambda _widgets, option, current, _language: shown.__setitem__(option.identifier, current)
mod = Mod()
model = panel_model.Model(mod)
names = ["focus", "pages", "notice", "close", "theme", "window_size", "EN", "FR", "restore", "undo", "enabled", "nav:omni_sprint",
         "nav:commands", "row:fov", "description:fov", "icons:PS5", "icons:XSX",
         "commands:settings", "commands:external"]
names += [f"nav:{key}" for key in panel_camera_pages.PAGES] + [f"{key}:settings" for key in panel_camera_pages.PAGES]
names += [f"{part}:{name}" for name in ("loot_reach", "shoulder_left", "shoulder_smooth", "orbit_smooth", "shoulder_seconds", "orbit", "third_person_ads", "orbit_distance")
          for part in ("row", "description")]
# The DYNAMIC CAMERA page's sliders, greyed under their switch (Kevin, 2026-10-06).
DYNAMIC_SLIDERS = {"speed_fov_gain": "speed_fov", "speed_fov_seconds": "speed_fov",
                   "action_framing_strength": "action_framing", "camera_motion_strength": "camera_motion"}
names += [f"{part}:{name}" for name in DYNAMIC_SLIDERS for part in ("row", "description")]
names += [f"setting:{key}" for key in model.options]
for action, device in camera_control_config.SLOTS:
    names += [f"command:{action}:{device}", f"clear:{action}:{device}", f"value:{action}:{device}"]
names += ["commands_reset", "commands_status"]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
fov = widgets["setting:fov"]
check("the FOV row is greyed while Custom FOV is off",
      fov.enabled is False and widgets["row:fov"].opacity < 1 and widgets["description:fov"].opacity < 1)
check("the shoulder needs third person, while Orbit and loot remain independent",
      all(widgets[f"setting:{name}"].enabled is False and widgets[f"row:{name}"].opacity < 1
          for name in ("shoulder_left",))
      and widgets['setting:orbit'].enabled is True
      and widgets["setting:loot_reach"].enabled is True and widgets["row:loot_reach"].opacity == 1.0)
widgets["setting:extended_loot"].checked = True
check("Extended Loot Reach off greys the loot reach",
      not form.poll() and widgets["setting:loot_reach"].enabled is False and widgets["row:loot_reach"].opacity < 1)
widgets["setting:extended_loot"].checked = True
widgets["setting:third_person"].checked = True
check("third person on brings the shoulder and the orbit camera back",
      not form.poll() and "extended_loot" not in form.pending and form.pending["third_person"] is True
      and all(widgets[f"setting:{name}"].enabled is True for name in ("shoulder_left", "orbit")))
distance = widgets["setting:orbit_distance"]
check("the Orbit distance is greyed while the orbit camera is off", distance.enabled is False
      and widgets["row:orbit_distance"].opacity < 1 and widgets["description:orbit_distance"].opacity < 1)
for third_person, orbit, live in ((True, True, True), (False, True, True), (True, False, False)):
    form.shown.update(third_person=third_person, orbit=orbit)
    form.refresh_dependency(widgets)
    check(f"the Orbit distance is {'live' if live else 'greyed'} with third person {third_person}, orbit {orbit}",
          distance.enabled is live)
form.shown.update(third_person=True, orbit=settings.orbit.value)
for slider, switch in DYNAMIC_SLIDERS.items():
    form.shown[switch] = False
    form.refresh_dependency(widgets)
    off = widgets[f"setting:{slider}"].enabled is False and widgets[f"row:{slider}"].opacity < 1
    form.shown[switch] = True
    form.refresh_dependency(widgets)
    check(f"{slider} is greyed while {switch} is off", off and widgets[f"setting:{slider}"].enabled is True)
form.refresh_dependency(widgets)
widgets["setting:third_person"].checked = True
form.poll()
check("camera shortcuts use their own immediate transaction", model.write_commands({"third_person_key": "J"})
      and settings.third_person_key.value == settings.third_person_bind.key == "J")

widgets["setting:custom_fov"].checked = True
check("Custom FOV on brings the FOV row back",
      not form.poll() and fov.enabled is True and widgets["row:fov"].opacity == 1.0)
fov.value = 125
form.poll()
form.changed_at -= panel_theme.SAVE_DELAY_NS
check("changes are saved on their own after the delay",
      not form.poll() and not form.pending and settings.custom_fov.value is True and settings.fov.value == 125
      and settings.third_person_key.value == "J")

widgets["setting:omni_sprint"].checked = True
form.poll()
form.changed_at -= panel_theme.SAVE_DELAY_NS
check("the sprint's switch turns the sprint off on its own, the camera settings untouched",
      not form.poll() and settings.omni_sprint.value is False and not settings.sprint_enabled()
      and settings.custom_fov.value is True)
widgets["nav:camera"].checked = True
check("CAMERA opens the second page", not form.poll() and widgets["pages"].active == 1 and model.page == "camera")
for index, key in enumerate(("aiming", "orbit_camera", "loot"), start=2):
    widgets[f"nav:{key}"].checked = True
    check(f"{key} opens page {index + 1}", not form.poll() and widgets["pages"].active == index and model.page == key)

widgets["FR"].checked = True
check("the header's FR button switches the language", not form.poll() and model.language == "FR")
settings.zoom.option.value = 450
widgets["restore"].checked = True
check("Restore puts the defaults back", not form.poll() and settings.custom_fov.value is False
      and settings.omni_sprint.value is True and settings.zoom.option.value == 300
      and settings.third_person_key.value == "P" and model.can_undo)
check("Restore takes the Orbit distance once, as a page setting",
      [option.identifier for option, _ in model._undo].count("orbit_distance") == 1)
widgets["undo"].checked = True
check("Undo gives them back", not form.poll() and settings.fov.value == 125 and settings.zoom.option.value == 450
      and not model.can_undo)

mod.fail = True
widgets["setting:third_person"].checked = True
form.poll()
widgets["close"].checked = True
check("a failed save keeps the window open", not form.poll() and settings.third_person.value is False)
mod.fail = False
check("failed compensation keeps the transaction owned", model.transaction.pending)
model.transaction.clock = lambda: model.transaction.retry_after + 1
check("confirmed compensation unlocks the menu", not form.poll() and not model.transaction.pending)
widgets["close"].checked = True
check("Close saves and closes", form.poll())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
