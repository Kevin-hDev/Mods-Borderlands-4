"""The camera command form keeps one bounded draft and saves a captured key immediately."""

from movement_test_result import Reporter

result = Reporter("camera command capture supports keyboard, controller, none and escape")

from types import SimpleNamespace

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement.camera_control_form import Form


class Widget:
    def __init__(self):
        self.checked = False
        self.selecting = False
        self.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="None"))

    def IsChecked(self): return self.checked
    def SetIsChecked(self, value): self.checked = value
    def GetIsSelectingKey(self): return self.selecting
    def SetIsEnabled(self, value): self.enabled = value
    def SetSelectedKey(self, value): self.SelectedKey = value
    def SetText(self, value): self.text = value


class Actions:
    def __init__(self): self.calls = []
    def assign(self, action, device, key): self.calls.append((action, device, key)); return key != "Tilde"
    def defaults(self): self.calls.append(("defaults",)); return True


names = []
for action in ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out"):
    for device in ("keyboard", "controller"):
        names += [f"command:{action}:{device}", f"clear:{action}:{device}", f"value:{action}:{device}"]
names += ["commands_reset", "commands_status"]
widgets = {name: Widget() for name in names}
# The real page also registers decorative icon/text widgets below each command selector.
widgets["command:shoulder:keyboard:icon"] = SimpleNamespace()
widgets["command:shoulder:keyboard:key_label"] = SimpleNamespace()
actions = Actions()
form = Form({name: (lambda item=item: item) for name, item in widgets.items()}, actions)
assert not form.selecting()
keyboard = widgets["command:shoulder:keyboard"]
keyboard.selecting = True
assert form.selecting() and not form.poll()
assert keyboard.enabled and not widgets["command:orbit:keyboard"].enabled
keyboard.selecting = False
keyboard.SelectedKey.Key.KeyName = "Six"
assert not form.poll() and actions.calls[-1] == ("shoulder", "keyboard", "Six")
widgets["clear:shoulder:keyboard"].checked = True
assert not form.poll() and actions.calls[-1] == ("shoulder", "keyboard", None)
keyboard.SelectedKey.Key.KeyName = "Escape"
before_cancel = len(actions.calls)
assert not form.poll() and len(actions.calls) == before_cancel
keyboard.SelectedKey.Key.KeyName = "LeftMouseButton"
assert not form.poll() and len(actions.calls) == before_cancel
widgets["commands_reset"].checked = True
assert not form.poll() and actions.calls[-1] == ("defaults",)
form.set_enabled(False)
assert not widgets["command:shoulder:keyboard"].enabled
assert not widgets["clear:orbit:controller"].enabled and not widgets["commands_reset"].enabled
form.set_enabled(True)
assert widgets["command:shoulder:keyboard"].enabled
assert len(form.draft) <= 3


class ModelActions:
    def __init__(self):
        self.command_actions = SimpleNamespace(last_status="refused")

    def assign_command(self, action, device, key):
        return False


refused_actions = ModelActions()
refused_form = Form({name: (lambda item=item: item) for name, item in widgets.items()}, refused_actions)
keyboard.SelectedKey.Key.KeyName = "Tilde"
assert not refused_form.poll() and refused_form.notice == "refused"
result.success()
