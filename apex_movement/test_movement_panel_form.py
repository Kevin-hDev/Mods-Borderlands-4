"""A click is never missed, and failed saves keep the Movement menu open."""

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import panel_form, panel_labels, panel_model, settings


class Widget:
    def __init__(self):
        self.checked = False
        self.value = 0.0
        self.active = 0

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

    def SetText(self, value):
        self.text = value


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
panel_labels.value = lambda *_: None
mod = Mod()
model = panel_model.Model(mod)
names = ["focus", "pages", "notice", "close", "EN", "FR", "restore", "undo", "enabled"]
names += [f"nav:{page}" for page in model.pages]
names += [f"setting:{key}" for key in model.options]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)

widgets["setting:dash"].checked = True
assert not form.poll() and form.pending == {"dash": False}
widgets["nav:glide"].checked = True
assert not form.poll() and settings.dash.value is False and model.page == "glide"
assert widgets["pages"].active == model.pages.index("glide")
widgets["FR"].checked = True
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
print("OK | Movement menu latches clicks, saves pages and keeps a failed close open")
