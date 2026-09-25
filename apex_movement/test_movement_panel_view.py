"""The full Movement window builds all ten pages in Grapple's approved frame."""

from movement_test_result import Reporter

result = Reporter("full Movement window builds ten pages and a scrolling sidebar")

from types import SimpleNamespace

import movement_ui_fixture

movement_ui_fixture.install()

import unrealsdk  # noqa: E402

from apex_movement import panel_assets, panel_fonts, panel_form, panel_model, panel_preferences  # noqa: E402
from apex_movement import panel_theme as theme, panel_view  # noqa: E402


class Struct:
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = Struct()
        setattr(self, name, value)
        return value


class Enum:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, member):
        return f"{self.name}.{member}"


class Widget:
    created = []

    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner
        self.children, self.slots, self.calls = [], [], {}
        self.Font = Struct()
        self.created.append(self)

    def __getattr__(self, name):
        if name.startswith("Set") or name.startswith("AddChild"):
            return lambda *args: self.call(name, args)
        if name[:1].isupper():
            value = Struct()
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def call(self, name, args):
        if name == "SetContent":
            self.children[:] = [args[0]]
        elif name.startswith("AddChild"):
            self.children.append(args[0])
            slot = Widget("Slot", self)
            self.slots.append(slot)
            return slot
        self.calls[name] = args


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
panel_assets.texture = lambda _world: None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

panel_preferences.last_page.value = len(panel_preferences.PAGE_KEYS) - 1
model = panel_model.Model(SimpleNamespace(is_enabled=True))
root, widgets = panel_view.build_view(SimpleNamespace(), model)
assert root.kind == "UserWidget"
assert root.WidgetTree.RootWidget.kind == "ScaleBox"
assert len(model.pages) == 10
assert len(widgets["pages"].children) == len(model.pages) + 1
assert model.page == "options" and widgets["focus"] is widgets["options"]
assert "EN" not in widgets and "FR" not in widgets
assert all(key in widgets for key in ("options", "language:EN", "language:FR"))
assert theme.BRAND == "APEX MOVEMENT"


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


# Mockup V2 Options page: tilted title, plain sentence, no empty sentence in the language card, switch-style
# language buttons with a gap, and a round gear.
assert widgets["options_title"].calls["SetRenderTransformAngle"] == (float(theme.TILT_TITLE),)
assert widgets["options_description"].Font.Size == theme.TEXT_MD * theme.PX_TO_POINTS
assert widgets["group:language"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
language_boxes = [node for node in Widget.created
                  if node.kind == "HorizontalBox" and len(node.children) == 2
                  and widgets["language:EN"] in walk(node.children[0])
                  and widgets["language:FR"] in walk(node.children[1])]
assert len(language_boxes) == 1 and language_boxes[0].slots[0].calls["SetPadding"][0].Right == theme.SPACE_3
assert sum(node.calls.get("SetMinDesiredWidth") == (float(theme.SWITCH_WIDTH),)
           for node in walk(language_boxes[0])) == 2
assert all(widgets[f"options_icon:{index}"].calls["SetBrush"][0].DrawAs == "ESlateBrushDrawType.RoundedBox"
           for index in (4, 5))
assert all(f"row:{key}" in widgets for key in ("third_person", "custom_fov", "fov"))
# Kevin's shortcut fields (2026-09-25): no row of their own, but the key then its Change button after the Third
# Person switch.
assert "row:third_person_key" not in widgets and "label:third_person_key" not in widgets
row = widgets["row:third_person"]
shown, change = widgets["key:third_person_key"], widgets["setting:third_person_key"]
assert len(row.children) == 4
assert shown in walk(row.children[2]) and change in walk(row.children[3])
assert shown.kind == change.kind == "InputKeySelector"
assert shown.calls["SetVisibility"] == ("ESlateVisibility.HitTestInvisible",)
assert change.calls["SetAllowGamepadKeys"] == (False,) and "SetVisibility" not in change.calls
assert row.slots[2].calls["SetSize"][0].SizeRule == "ESlateSizeRule.Fill"
assert row.slots[2].calls["SetPadding"][0].Bottom == theme.SHADOW_SM
assert row.slots[3].calls["SetPadding"][0].Left == theme.SPACE_3
fit = [node for node in walk(row.children[2]) if node.kind == "ScaleBox"]
assert len(fit) == 1 and fit[0].calls["SetStretchDirection"] == ("EStretchDirection.DownOnly",)
assert any(node.calls.get("SetMinDesiredWidth") == (float(theme.KEY_CHANGE_WIDTH),) for node in walk(row.children[3]))
# The walk key sits the same way on its switch's row, on the auto sprint's page (Kevin, 2026-09-25).
assert "row:walk_key" not in widgets and "label:walk_key" not in widgets
walk_row = widgets["row:walk"]
walk_shown, walk_change = widgets["key:walk_key"], widgets["setting:walk_key"]
assert len(walk_row.children) == 4
assert walk_shown in walk(walk_row.children[2]) and walk_change in walk(walk_row.children[3])

# The form names the saved key in the key field; both selectors speak the menu's language.
for group in model.groups:
    group.description = group.identifier  # The SDK fake has no group description.
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
assert shown.calls["SetSelectedKey"][0].Key.KeyName == "P"
assert walk_shown.calls["SetSelectedKey"][0].Key.KeyName == "CapsLock"
# As the FOV under Custom FOV: the key's speed fades while the walk key is off, since it then changes nothing.
speed_row = ("row:walk_key_speed", "description:walk_key_speed")
assert all(widgets[name].calls["SetRenderOpacity"] == (1.0,) for name in speed_row)
form.shown["walk"] = False
form.refresh_dependency(form.resolve())
assert widgets["setting:walk_key_speed"].calls["SetIsEnabled"] == (False,)
assert all(widgets[name].calls["SetRenderOpacity"] == (theme.OPACITY_DISABLED,) for name in speed_row)
form.shown["walk"] = True
form.refresh_dependency(form.resolve())
assert change.calls["SetNoKeySpecifiedText"] == ("CHANGE",) and change.calls["SetKeySelectionText"] == ("PRESS A KEY",)
assert shown.calls["SetNoKeySpecifiedText"] == ("NONE",) and "SetSelectedKey" not in change.calls
panel_preferences.french.value = True
form.refresh_labels(form.resolve())
assert change.calls["SetNoKeySpecifiedText"] == ("MODIFIER",)
assert change.calls["SetKeySelectionText"] == ("APPUIE SUR UNE TOUCHE",)
assert shown.calls["SetNoKeySpecifiedText"] == ("AUCUNE",)

attached = set()


def visit(node):
    assert id(node) not in attached, "a widget is attached twice"
    attached.add(id(node))
    for child in node.children:
        visit(child)


visit(root.WidgetTree.RootWidget)
assert all(id(widget) in attached for widget in widgets.values())
assert sum(node.kind == "ScrollBox" for node in Widget.created) == len(model.pages) + 2
assert all(f"setting:{key}" in widgets for key in model.options)
assert len(widgets) < 450, "each widget is resolved during every menu poll"
result.success()
