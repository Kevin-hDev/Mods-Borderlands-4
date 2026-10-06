"""A click is never missed, and failed saves keep the Vehicle Driving menu open; on the CAMERA page, the arrows choose
the view and the key's card captures, clears and resets the view key."""

import types

import sdk_stubs

sdk_stubs.install()

from vehicle_driving import control_config, panel_form, panel_labels, panel_model, settings, view_key


def chord(key):
    return types.SimpleNamespace(Key=types.SimpleNamespace(KeyName=key))


class Widget:
    def __init__(self):
        self.checked = False
        self.value = 0.0
        self.active = 0
        self.enabled = True
        self.selecting = False
        self.SelectedKey = chord("None")

    def SetIsEnabled(self, value):
        self.enabled = value

    def GetIsSelectingKey(self):
        return self.selecting

    def SetSelectedKey(self, value):
        self.SelectedKey = value

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
names = ["focus", "pages", "notice", "close", "theme", "window_size", "EN", "FR", "restore", "undo", "enabled"]
names += [f"nav:{page}" for page in model.pages]
names += [f"setting:{key}" for key in model.options]
names += [f'vehicles:{key}' for key in ('standard', 'promotions', 'shatterland')]
names += ["setting:vehicle_view:previous", "setting:vehicle_view:next", "commands_reset", "commands_status",
          "icons:PS5", "icons:XSX"]
names += [f"{kind}:{action}:{device}" for action, device in control_config.SLOTS for kind in ("command", "clear")]
widgets = {name: Widget() for name in names}
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)

widgets["setting:grip"].checked = True
assert not form.poll() and form.pending == {"grip": False}
widgets["nav:handling"].checked = True
assert not form.poll() and settings.grip.value is False and model.page == "handling"
assert widgets["pages"].active == model.pages.index("handling")
widgets["FR"].checked = True
assert not form.poll() and model.language == "FR"
widgets["restore"].checked = True
assert not form.poll() and settings.grip.value is True and model.can_undo
widgets["undo"].checked = True
assert not form.poll() and settings.grip.value is False and not model.can_undo

# The CAMERA page (Kevin, 2026-10-06).
widgets["nav:camera"].checked = True
assert not form.poll() and model.page == "camera"
widgets["setting:vehicle_view:next"].checked = True
assert not form.poll() and form.pending == {"vehicle_view": "Close"}, "the next arrow goes to the next view"
widgets["setting:vehicle_view:previous"].checked = True
widgets["setting:vehicle_view:previous"].checked = True
form.poll()
assert form.pending == {}, "two clicks read once: back one view, the one saved"
widgets["setting:vehicle_view:previous"].checked = True
form.poll()
assert form.pending == {"vehicle_view": "Far"}, "before the game's view comes Far"
assert form.flush(form.resolve()) and settings.vehicle_view.value == "Far", "the view chosen is saved"
saves = mod.saved
widgets["command:view:keyboard"].SelectedKey = chord("K")
assert not form.poll() and view_key.keyboard_key.value == "K" and view_key.keyboard_bind.key == "K"
assert mod.saved == saves + 1 and form.command_form.notice == "saved", "a key captured is saved at once"
assert widgets["command:view:keyboard"].SelectedKey.Key.KeyName == "None", "the field is cleared for the next one"
widgets["command:view:keyboard"].SelectedKey = chord("Tilde")
assert not form.poll() and view_key.keyboard_key.value == "K" and form.command_form.notice == "reserved_key"
widgets["command:view:controller"].SelectedKey = chord("Gamepad_DPad_Up")
assert not form.poll() and view_key.controller_key.value == "Gamepad_DPad_Up"
widgets["clear:view:keyboard"].checked = True
assert not form.poll() and view_key.keyboard_key.value is None, "NONE leaves the view without a keyboard key"
widgets["commands_reset"].checked = True
assert not form.poll() and view_key.keyboard_key.value == "L" and view_key.controller_key.value is None
assert form.command_form.notice == "controls_reset", "the reset puts L back, and no controller button"
widgets["icons:XSX"].checked = True
assert not form.poll() and model.controller_icons == "XSX"
widgets["command:view:keyboard"].selecting = True
assert form.selecting(), "a key being captured keeps Escape for the capture"
widgets["command:view:keyboard"].selecting = False
widgets["nav:driving"].checked = True
assert not form.poll() and not form.selecting()
settings.vehicle_view.value = "Default"

mod.fail = True
widgets["setting:max_speed"].value = 150
widgets["close"].checked = True
assert not form.poll() and settings.max_speed.value == 125
mod.fail = False
assert model.transaction.pending
model.transaction.clock = lambda: model.transaction.retry_after + 1
assert not form.poll() and not model.transaction.pending
widgets["close"].checked = True
assert form.poll()
print("OK | Vehicle Driving menu latches clicks, saves pages and keeps a failed close open")
print("RESULTAT: TOUS LES TESTS PASSENT")
