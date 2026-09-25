"""A click is never missed, and failed saves keep the Movement menu open."""

from movement_test_result import Reporter

result = Reporter("Movement menu latches clicks, saves pages and keeps a failed close open")

from types import SimpleNamespace

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import panel_form, panel_labels, panel_model, panel_theme, settings


class Widget:
    def __init__(self):
        self.checked = False
        self.value = 0.0
        self.active = 0
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
shown = {}  # What the labels would show beside each setting: for the shortcut, the key in its key field.
panel_labels.value = lambda _widgets, option, current, _language: shown.__setitem__(option.identifier, current)
mod = Mod()
model = panel_model.Model(mod)
names = ["focus", "pages", "notice", "close", "options", "language:EN", "language:FR",
         "restore", "undo", "enabled", "row:fov", "description:fov",
         "row:walk_key_speed", "description:walk_key_speed"]
names += [f"nav:{page}" for page in model.pages]
names += [f"setting:{key}" for key in model.options]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
change = widgets["setting:third_person_key"]
assert shown["third_person_key"] == "P" and change.SelectedKey.Key.KeyName == "None"
assert widgets["setting:fov"].enabled is False
assert widgets["row:fov"].opacity < 1 and widgets["description:fov"].opacity < 1
# The walk key is on by default: its speed is live.
assert widgets["setting:walk_key_speed"].enabled is True and widgets["row:walk_key_speed"].opacity == 1.0
widgets["setting:walk"].checked = True
assert not form.poll() and form.pending["walk"] is False
assert widgets["setting:walk_key_speed"].enabled is False and widgets["row:walk_key_speed"].opacity < 1
widgets["setting:walk"].checked = True
assert not form.poll() and "walk" not in form.pending and widgets["row:walk_key_speed"].opacity == 1.0

widgets["options"].checked = True
assert not form.poll() and widgets["pages"].active == len(model.pages)
assert form.options_open
assert model.page == "options"
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
assert form.options_open and widgets["pages"].active == len(model.pages)
# A captured key moves to the key field and the Change button shows its own word again.
change.SelectedKey.Key.KeyName = "K"
assert not form.poll() and form.pending["third_person_key"] == "K"
assert shown["third_person_key"] == "K" and change.SelectedKey.Key.KeyName == "None"
# Nothing is read while the button still waits for a key.
change.selecting = True
change.SelectedKey.Key.KeyName = "J"
assert form.selecting() and not form.poll() and form.pending["third_person_key"] == "K"
assert change.SelectedKey.Key.KeyName == "J"
change.selecting = False
assert not form.selecting() and not form.poll() and form.pending["third_person_key"] == "J"
# A second click on the button cancels, like Escape: the key stays and no failure is reported.
change.SelectedKey.Key.KeyName = "LeftMouseButton"
assert not form.poll() and form.pending["third_person_key"] == "J" and form.notice != "failed"
assert shown["third_person_key"] == "J" and change.SelectedKey.Key.KeyName == "None"
# A refused key keeps the previous one, says so, and frees the button.
change.SelectedKey.Key.KeyName = "Tilde"
assert not form.poll() and form.pending["third_person_key"] == "J" and form.notice == "failed"
assert shown["third_person_key"] == "J" and change.SelectedKey.Key.KeyName == "None"
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
widgets["restore"].checked = True
assert not form.poll() and settings.dash.value is True and model.can_undo
widgets["undo"].checked = True
assert not form.poll() and settings.dash.value is False and not model.can_undo

mod.fail = True
widgets["setting:dash_distance"].value = 230
widgets["close"].checked = True
assert not form.poll() and settings.dash_distance.value == 200
mod.fail = False
widgets["close"].checked = True
assert form.poll()
result.success()
