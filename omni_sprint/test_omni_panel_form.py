"""Omni Sprint's window reads each click once: the shortcut's capture, the FOV row's grey, languages and saves."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from omni_sprint import panel_form, panel_labels, panel_model, panel_theme, settings  # noqa: E402

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
shown = {}  # What the labels would show beside each setting: for the shortcut, the key in its key field.
panel_labels.value = lambda _widgets, option, current, _language: shown.__setitem__(option.identifier, current)
mod = Mod()
model = panel_model.Model(mod)
names = ["focus", "pages", "notice", "close", "EN", "FR", "restore", "undo", "enabled", "nav:omni_sprint",
         "nav:camera", "row:fov", "description:fov"]
names += [f"setting:{key}" for key in model.options]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
change, fov = widgets["setting:third_person_key"], widgets["setting:fov"]
check("the saved key shows in the key field, and the Change button keeps its own word",
      shown["third_person_key"] == "P" and change.SelectedKey.Key.KeyName == "None")
check("the FOV row is greyed while Custom FOV is off",
      fov.enabled is False and widgets["row:fov"].opacity < 1 and widgets["description:fov"].opacity < 1)

change.SelectedKey.Key.KeyName = "K"
check("a captured key moves to the key field and frees the button",
      not form.poll() and form.pending["third_person_key"] == "K" and shown["third_person_key"] == "K"
      and change.SelectedKey.Key.KeyName == "None")
change.selecting = True
change.SelectedKey.Key.KeyName = "J"
check("nothing is read while the button still waits for a key",
      form.selecting() and not form.poll() and form.pending["third_person_key"] == "K")
change.selecting = False
check("the key pressed is read once the wait ends", not form.selecting() and not form.poll()
      and form.pending["third_person_key"] == "J")
change.SelectedKey.Key.KeyName = "LeftMouseButton"
check("a second click on the button cancels like Escape, with no failure",
      not form.poll() and form.pending["third_person_key"] == "J" and form.notice != "failed")
change.SelectedKey.Key.KeyName = "Tilde"
check("a refused key keeps the previous one and says so",
      not form.poll() and form.pending["third_person_key"] == "J" and form.notice == "failed"
      and change.SelectedKey.Key.KeyName == "None")

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

widgets["FR"].checked = True
check("the header's FR button switches the language", not form.poll() and model.language == "FR")
widgets["restore"].checked = True
check("Restore puts the defaults back", not form.poll() and settings.custom_fov.value is False
      and settings.omni_sprint.value is True
      and settings.third_person_key.value == "P" and model.can_undo)
widgets["undo"].checked = True
check("Undo gives them back", not form.poll() and settings.fov.value == 125 and not model.can_undo)

mod.fail = True
widgets["setting:third_person"].checked = True
form.poll()
widgets["close"].checked = True
check("a failed save keeps the window open", not form.poll() and settings.third_person.value is False)
mod.fail = False
widgets["close"].checked = True
check("Close saves and closes", form.poll())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
