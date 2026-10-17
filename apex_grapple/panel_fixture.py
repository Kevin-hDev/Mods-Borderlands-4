"""Widget doubles for full-menu interaction tests; no rendering claims."""

from types import SimpleNamespace as NS
import control_fixture as f
import unrealsdk
import apex_grapple
from apex_grapple import menu, panel_choices, panel_factory, panel_form, panel_model, panel_preferences, panel_theme
from apex_grapple import updates

BUTTON_PARTS = ("", "_label", "_fill", "_frame", "_shadow")
unrealsdk.find_enum = lambda name: NS(Visible="Visible", Collapsed="Collapsed",
                                    HitTestInvisible="HitTestInvisible")


class Widget:
    def __init__(self):
        self.checked, self.selecting, self.enabled, self.opacity = False, False, True, 1.0
        self.text, self.value, self.index, self.percent = "", 0.0, 0, None
        self.brush = self.color = None
        self.visibility, self.text_visibility, self.icon_brush = "Visible", "Visible", None
        self.SelectedKey = NS(Key=NS(KeyName="None"))

    def SetText(self, text):
        self.text = text

    def SetVisibility(self, value):
        self.visibility = value

    def SetTextBlockVisibility(self, value):
        self.text_visibility = value

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
    """Every widget name the view registers, derived the way panel_view builds them: a row of a settings page
    registered whole, a button per choice of a spinner or two arrows and the name's boxes for a row of menu.ARROWS,
    the sentence and its frame on a page of menu.NOTICES, and the update notes' pop-up (panel_updates.py)."""
    found = {"focus", "first", "second", "pages", "status", "current", "settings_caption", "meta", "notice",
             "escape_hint", "tag", "two_text"}
    found.update(("icons_label", "pad_summary", "pad_label", "pad_first", "pad_second",
                  "pad_separator", "pad_second_box", "first:icon", "second:icon",
                  "first:key_label", "second:key_label"))
    buttons = ["window_size", "theme", *panel_preferences.LANGUAGES, "close", "restore", "undo", "enabled", "two",
               "reset"]
    buttons += [f"nav:{page}" for page in panel_theme.PAGES]
    buttons += ["icons:PS5", "icons:XSX"]
    found.update(("popups", "popup:updates", "popup:updates:beside", "heading:popup_updates", "group:popup_updates",
                  "updates_points", "updates_next_box"))
    buttons += ["popup:updates:close", "updates_next"]
    for page in panel_theme.PAGES:
        found.update((f"heading:{page}", f"group:{page}"))
    found.update(f"row:{option.identifier}" for group in model.groups for option in group.children)
    for key, option in model.options.items():
        found.update((f"label:{key}", f"description:{key}"))
        if type(option.default_value) is bool:
            buttons.append(f"setting:{key}")
        elif panel_choices.is_choice(option) and key in getattr(menu, "ARROWS", ()):
            found.update((f"setting:{key}", f"choice:{key}", f"value:{key}"))
            buttons += [f"setting:{key}:{name}" for name, _, _ in panel_choices.ARROWS]
        elif panel_choices.is_choice(option):
            found.add(f"setting:{key}")
            buttons += [f"setting:{key}:{choice}" for choice in option.choices]
        else:
            found.update((f"setting:{key}", f"value:{key}", f"fill:{key}"))
    found.update(f"{kind}:{page}" for page in menu.NOTICES for kind in ("notice", "notice_frame"))
    found.update(name + part for name in buttons for part in BUTTON_PARTS)
    return found


# The windows the tests open are a player's who saw this version's notes: test_update_notes.py opens the others'.
updates.seen.value = apex_grapple.__version__


def create():
    model = panel_model.Model(f.mod)
    widgets = {name: Widget() for name in names(model)}
    refs = {name: lambda widget=widget: widget for name, widget in widgets.items()}
    form = panel_form.PanelForm(refs, panel_factory.PanelBindings(), model)
    return widgets, form
