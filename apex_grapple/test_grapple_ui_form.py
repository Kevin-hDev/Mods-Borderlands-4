"""A complete choice saves once; close/partial/failed/reset states stay distinct."""

import copy
import sys
from types import ModuleType, SimpleNamespace as NS
from ui_test_loader import load

sdk = ModuleType("unrealsdk")
sdk.make_struct = lambda name, **kwargs: NS(**kwargs)
sdk.logging = NS(info=lambda message: None)
sys.modules["unrealsdk"] = sdk
Form = load("control_form").Form


class Widget:
    def __init__(self):
        self.checked, self.selecting, self.enabled, self.text = False, False, True, ""
        self.SelectedKey = NS(Key=NS(KeyName="None"))

    def IsChecked(self):
        return self.checked

    def SetIsChecked(self, value):
        self.checked = value

    def GetIsSelectingKey(self):
        return self.selecting

    def SetSelectedKey(self, value):
        self.SelectedKey = copy.deepcopy(value)

    def SetIsEnabled(self, value):
        self.enabled = value

    def SetText(self, value):
        self.text = value


class Bindings:
    def __init__(self):
        self.saved, self.resets, self.fail = [], 0, False

    def save(self, chosen):
        self.saved.append(chosen)
        return not self.fail, "Failed" if self.fail else "Saved"

    def reset(self):
        self.resets += 1
        return not self.fail, "Failed" if self.fail else "Reset"

    def summary(self):
        return "Active controls"


def create():
    widgets = {name: Widget() for name in ("first", "second", "two", "close", "reset", "status", "current")}
    bindings = Bindings()
    form = Form({name: lambda item=item: item for name, item in widgets.items()}, bindings)
    return widgets, bindings, form


w, b, form = create()
w["first"].SelectedKey.Key.KeyName = "V"
assert not form.poll() and b.saved == [("V",)] and w["status"].text == "Saved"
form.poll()
assert len(b.saved) == 1
w["close"].checked = True
assert form.poll() and len(b.saved) == 1

w, b, form = create()
w["two"].checked = True
form.poll()
w["first"].SelectedKey.Key.KeyName = "V"
form.poll()
assert not b.saved
w["second"].SelectedKey.Key.KeyName = "G"
form.poll()
assert b.saved == [("V", "G")]
w["reset"].checked = True
assert not form.poll() and b.resets == 1 and not w["reset"].checked
assert w["first"].SelectedKey.Key.KeyName == "None" and not w["two"].checked
form.poll()
assert b.resets == 1 and len(b.saved) == 1

w, b, form = create()
b.fail = True
w["first"].SelectedKey.Key.KeyName = "V"
form.poll()
assert w["status"].text == "Failed"
form.poll()
assert len(b.saved) == 1
w["first"].selecting = True
assert form.selecting()
w["close"].checked = True
assert form.poll()  # Close has priority over a selection arriving in the same frame.
print("OK | save once, partial chord, close priority, reset, failed-save status")
