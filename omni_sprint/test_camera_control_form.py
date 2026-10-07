"""Omni Sprint receives the generated bounded capture form."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs

sdk_stubs.install()

from omni_sprint.camera_control_form import Form


class Widget:
    def __init__(self):
        self.checked = self.selecting = False
        self.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="None"))
    def IsChecked(self): return self.checked
    def SetIsChecked(self, value): self.checked = value
    def GetIsSelectingKey(self): return self.selecting
    def SetIsEnabled(self, value): self.enabled = value
    def SetSelectedKey(self, value): self.SelectedKey = value
    def SetText(self, value): self.text = value


class Actions:
    def __init__(self): self.calls = []
    def assign(self, action, device, key): self.calls.append((action, device, key)); return True
    def defaults(self): return True


names = [f"{kind}:{action}:{device}" for action in ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out", "free_look", "camera_distance")
         for device in ("keyboard", "controller") for kind in ("command", "clear")]
names += ["commands_reset", "commands_status"]
widgets = {name: Widget() for name in names}
actions = Actions()
form = Form({name: (lambda item=item: item) for name, item in widgets.items()}, actions)
chosen = widgets["command:orbit:controller"]
chosen.SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
assert actions.calls == [("orbit", "controller", "Gamepad_FaceButton_Top")] and not form.draft
print("RESULTAT: OK")
