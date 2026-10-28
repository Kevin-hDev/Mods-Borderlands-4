"""Widget doubles for the window's interaction tests, as Apex Heirloom's panel_fixture.py; no rendering claims.

The names below are those the window's view registers: test_panel_view.py builds the real view and checks they are the
same, so a form tested here reads no widget the game would not have.
"""

from types import SimpleNamespace as NS

import sdk_stubs

state = sdk_stubs.install()

from benefix_ohm_attack import control_config, menu, mod, panel_choices, panel_form, panel_model  # noqa: E402
from benefix_ohm_attack import panel_theme  # noqa: E402

BUTTON_PARTS = ("", "_label", "_fill", "_frame", "_shadow")


class Widget:
    def __init__(self):
        self.checked, self.selecting, self.enabled = False, False, True
        self.text, self.value, self.index, self.percent, self.opacity = "", 0.0, 0, None, 1.0
        self.brush = self.color = None
        self.visibility, self.icon_brush = "Visible", None
        self.placeholder = self.listening = None
        self.SelectedKey = NS(Key=NS(KeyName="None"))

    def SetText(self, text):
        self.text = text

    def SetVisibility(self, value):
        self.visibility = value

    def SetBrush(self, value):
        self.icon_brush = value

    def IsChecked(self):
        return self.checked

    def SetIsChecked(self, value):
        self.checked = value

    def SetIsEnabled(self, value):
        self.enabled = value

    def SetRenderOpacity(self, value):
        self.opacity = value

    def SetValue(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def SetPercent(self, value):
        self.percent = value

    def SetBrushColor(self, value):
        self.brush = value

    def SetColorAndOpacity(self, value):
        self.color = value

    def SetActiveWidgetIndex(self, value):
        self.index = value

    def SetNoKeySpecifiedText(self, value):
        self.placeholder = value

    def SetKeySelectionText(self, value):
        self.listening = value

    def SetSelectedKey(self, value):
        self.SelectedKey = NS(Key=NS(KeyName=value.Key.KeyName))

    def GetIsSelectingKey(self):
        return self.selecting


def names(model):
    """Every widget name the view registers: a title and a sentence per card, a row per setting (two arrows around a
    name, a switch or a slider), each row in a box of its own; on the COMMANDS page a card per command, each row with
    its selector, its NONE and its value, then the icons and the reset."""
    found = {"focus", "pages", "settings_caption", "meta", "notice", "escape_hint", "tag", "icons_label",
             "commands_status"}
    buttons = ["window_size", "theme", "EN", "FR", "close", "restore", "undo", "enabled", "commands_reset", "icons:PS5", "icons:XSX"]
    buttons += [f"nav:{page}" for page in panel_theme.PAGES]
    for cards in menu.CARDS.values():
        for card, _ in cards:
            found.update((f"heading:{card}", f"group:{card}"))
    for command in control_config.COMMANDS:
        key = f"command_{command.name}"
        found.update((f"heading:{key}", f"group:{key}", f"card:{key}"))
        for device in ("keyboard", "controller"):
            slot = f"{command.name}:{device}"
            found.update((f"device:{slot}", f"command:{slot}", f"command:{slot}:icon", f"command:{slot}:key_label",
                          f"value:{slot}", f"value:{slot}:icon"))
            buttons.append(f"clear:{slot}")
    for key, option in model.options.items():
        found.update((f"label:{key}", f"description:{key}", f"row:{key}", f"block:{key}"))
        if type(option.default_value) is bool:
            buttons.append(f"setting:{key}")
        elif key in menu.ARROWS:
            found.update((f"setting:{key}", f"choice:{key}", f"value:{key}"))
            buttons += [f"setting:{key}:previous", f"setting:{key}:next"]
        elif panel_choices.is_choice(option):
            found.add(f"setting:{key}")
            buttons += [f"setting:{key}:{choice}" for choice in option.choices]
        else:
            found.update((f"setting:{key}", f"value:{key}", f"fill:{key}"))
    found.update(name + part for name in buttons for part in BUTTON_PARTS)
    return found


def create():
    model = panel_model.Model(mod)
    widgets = {name: Widget() for name in names(model)}
    refs = {name: lambda widget=widget: widget for name, widget in widgets.items()}
    form = panel_form.PanelForm(refs, model)
    return widgets, form
