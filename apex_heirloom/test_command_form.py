"""Tests the COMMANDS page's capture form, Apex Movement's: a captured key or a cleared one is saved at once, Escape and
the left click cancel without a word, the other rows wait while one captures; the reset says the keys are back; a
blocked command, its card greyed with its part, is neither chosen nor cleared, and comes back live."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom.command_form import Form  # noqa: E402
from apex_heirloom.control_config import SLOTS  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Widget:
    def __init__(self):
        self.checked = self.selecting = False
        self.enabled = True
        self.text = ""
        self.SelectedKey = NS(Key=NS(KeyName="None"))

    def IsChecked(self):
        return self.checked

    def SetIsChecked(self, value):
        self.checked = value

    def GetIsSelectingKey(self):
        return self.selecting

    def SetIsEnabled(self, value):
        self.enabled = value

    def SetSelectedKey(self, value):
        self.SelectedKey = NS(Key=NS(KeyName=value.Key.KeyName))

    def SetText(self, value):
        self.text = value


class Model:
    """The window's model as the form calls it: its commands' saves, their last status."""

    def __init__(self):
        self.calls, self.command_actions = [], NS(last_status="ready")

    def assign_command(self, action, device, key):
        self.calls.append((action, device, key))
        self.command_actions.last_status = "duplicate_put_away" if key == "Q" else "saved"
        return key != "Q"

    def default_commands(self):
        self.calls.append(("defaults",))
        return True


names = ["commands_reset", "commands_status"]
names += [f"{kind}:{action}:{device}" for action, device in SLOTS for kind in ("command", "clear")]
widgets = {name: Widget() for name in names}
model = Model()
form = Form({name: (lambda item=item: item) for name, item in widgets.items()}, model)
inspect_key = widgets["command:inspect:keyboard"]

inspect_key.selecting = True
check("while one row captures, the others wait", form.selecting() and not form.poll() and inspect_key.enabled
      and not widgets["command:put_away:keyboard"].enabled and not widgets["command:inspect:controller"].enabled)
inspect_key.selecting = False
inspect_key.SelectedKey.Key.KeyName = "F"
form.poll()
check("a captured key is saved at once to its command and device, the row made ready again",
      model.calls[-1] == ("inspect", "keyboard", "F") and form.notice == "saved" and form.changed
      and inspect_key.SelectedKey.Key.KeyName == "None" and widgets["command:put_away:keyboard"].enabled)
inspect_key.SelectedKey.Key.KeyName = "Q"
form.poll()
check("a key refused says the model's cause", model.calls[-1] == ("inspect", "keyboard", "Q")
      and form.notice == "duplicate_put_away" and widgets["commands_status"].text == "duplicate_put_away")
widgets["clear:inspect:controller"].checked = True
form.poll()
check("NONE clears the row's key", model.calls[-1] == ("inspect", "controller", None))
calls = len(model.calls)
for cancel in ("Escape", "LeftMouseButton"):
    inspect_key.SelectedKey.Key.KeyName = cancel
    form.poll()
check("Escape and the left click cancel the capture without a word or a save",
      len(model.calls) == calls and inspect_key.SelectedKey.Key.KeyName == "None")
widgets["commands_reset"].checked = True
form.poll()
check("the reset of the keys says they are back, not that it can be undone",
      model.calls[-1] == ("defaults",) and form.notice == "controls_reset")

form.block(widgets, "inspect", True)
check("a blocked command's rows are stilled, selector and NONE, the other command's live",
      not inspect_key.enabled and not widgets["clear:inspect:keyboard"].enabled
      and not widgets["command:inspect:controller"].enabled and widgets["command:put_away:keyboard"].enabled
      and widgets["clear:put_away:controller"].enabled)
calls = len(model.calls)
widgets["clear:inspect:keyboard"].checked = True
inspect_key.SelectedKey.Key.KeyName = "G"
form.poll()
check("and a poll neither brings them back nor saves anything for them", not inspect_key.enabled
      and len(model.calls) == calls and widgets["command:put_away:keyboard"].enabled)
widgets["command:put_away:controller"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
check("the other command's key is still saved", model.calls[-1] == ("put_away", "controller", "Gamepad_FaceButton_Top"))
# A stilled button cannot be clicked in the game: what the test put there goes before the card comes back.
widgets["clear:inspect:keyboard"].checked = False
inspect_key.SelectedKey.Key.KeyName = "None"
form.block(widgets, "inspect", False)
form.poll()
check("unblocked, its rows are live again", inspect_key.enabled and widgets["clear:inspect:keyboard"].enabled)
inspect_key.SelectedKey.Key.KeyName = "H"
form.poll()
check("... and a key captured there is saved", model.calls[-1] == ("inspect", "keyboard", "H"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
