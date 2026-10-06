"""The full Movement window builds its settings and camera commands pages in Grapple's frame."""

from movement_test_result import Reporter

result = Reporter("full Movement window builds settings and camera command pages in a scrolling sidebar")

from types import SimpleNamespace

import movement_ui_fixture

movement_ui_fixture.install()

import unrealsdk  # noqa: E402

from apex_movement import camera_settings, panel_assets, panel_fonts, panel_form, panel_model, panel_preferences  # noqa: E402
from apex_movement import panel_theme as theme, panel_view, panel_widgets as w  # noqa: E402


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

    def IsChecked(self):
        return self.calls.get("SetIsChecked", (False,))[0]

    def GetValue(self):
        return self.calls.get("SetValue", (0.0,))[0]

    def GetIsSelectingKey(self):
        # Waiting for a key, as far as a poll can tell: the fake's saved key is no name a shortcut could take.
        return True


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
panel_assets.texture = lambda _world: None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

panel_preferences.last_page.value = panel_preferences.PAGE_KEYS.index("options")
camera_settings.shoulder_controller.value = "Gamepad_FaceButton_Top"
model = panel_model.Model(SimpleNamespace(is_enabled=True))
root, widgets = panel_view.build_view(SimpleNamespace(), model)
assert root.kind == "UserWidget"
# The window sits on a clear layer over the whole screen (panel_modal, 2026-10-06).
assert (root.WidgetTree.RootWidget.kind == "CanvasPanel"
        and [child.kind for child in root.WidgetTree.RootWidget.children] == ["BackgroundBlur", "ScaleBox"])
assert len(model.pages) == 13 and model.pages[-3:] == ("commands", "language", "dynamic_camera")
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
assert widgets["options_title:options"].calls["SetRenderTransformAngle"] == (float(theme.TILT_TITLE),)
assert widgets["options_description:options"].Font.Size == theme.TEXT_MD * theme.PX_TO_POINTS
assert widgets["group:language"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
language_boxes = [node for node in Widget.created
                  if node.kind == "HorizontalBox" and len(node.children) == 2
                  and widgets["language:EN"] in walk(node.children[0])
                  and widgets["language:FR"] in walk(node.children[1])]
assert len(language_boxes) == 1 and language_boxes[0].slots[0].calls["SetPadding"][0].Right == theme.SPACE_3
# The sidebar's side padding lies inside its ScrollBox, which cuts whatever leaves it: the slanted page buttons lean
# past their box, and their corners were cut (Kevin's screenshot, 2026-10-06).
sidebar_scroll = next(node for node in Widget.created
                      if node.kind == "ScrollBox" and widgets[f"nav:{theme.PAGES[0]}"] in walk(node))
inside = sidebar_scroll.slots[0].calls["SetPadding"][0]
assert inside.Left >= theme.SPACE_4 and inside.Right >= theme.SPACE_4, "the page buttons' corners stay whole"
assert sum(node.calls.get("SetMinDesiredWidth") == (float(theme.SWITCH_WIDTH),)
           for node in walk(language_boxes[0])) == 2
assert all(widgets[f"options_icon:{index}"].calls["SetBrush"][0].DrawAs == "ESlateBrushDrawType.RoundedBox"
           for index in (4, 5))
assert all(f"row:{key}" in widgets for key in
           ("third_person", "shoulder_left", "orbit", "custom_fov", "fov"))
# Camera shortcuts have left the Camera card: the dedicated page owns three cards and two device rows each.
assert all(f"setting:{key}" not in widgets for key in
           ("third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
            "orbit_key", "orbit_controller"))
for action in ("third_person", "shoulder", "orbit"):
    assert f"heading:command_{action}" in widgets
    for device in ("keyboard", "controller"):
        selector = widgets[f"command:{action}:{device}"]
        assert selector.kind == "InputKeySelector"
        assert selector.calls["SetEscapeKeys"][0][0].KeyName == "Escape"
        selector_box = next(node for node in Widget.created if node.kind == "SizeBox"
                            and any(child.kind == "Overlay" and selector in child.children
                                    for child in node.children))
        assert selector_box.calls["SetWidthOverride"] == (float(theme.KEY_CHANGE_WIDTH),)
        assert f"clear:{action}:{device}" in widgets and f"value:{action}:{device}" in widgets
# The slow walk key sits the same way on its switch's row, on the Movement page (Kevin, 2026-09-25 and 26).
assert "row:walk_key" not in widgets and "label:walk_key" not in widgets
walk_row = widgets["row:walk"]
walk_shown, walk_change = widgets["key:walk_key"], widgets["setting:walk_key"]
assert len(walk_row.children) == 4
assert walk_shown in walk(walk_row.children[2]) and walk_change in walk(walk_row.children[3])

# The form names the saved key in the key field; both selectors speak the menu's language.
for group in model.groups:
    group.description = group.identifier  # The SDK fake has no group description.
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
assert walk_shown.calls["SetSelectedKey"][0].Key.KeyName == "CapsLock"
assert widgets["setting:shoulder_left_label"].calls["SetText"] == ("RIGHT",)
# As the FOV under Custom FOV: the key's speed fades while the walk key is off, since it then changes nothing.
speed_row = ("row:walk_key_speed", "description:walk_key_speed")
assert all(widgets[name].calls["SetRenderOpacity"] == (1.0,) for name in speed_row)
form.shown["walk"] = False
form.refresh_dependency(form.resolve())
assert widgets["setting:walk_key_speed"].calls["SetIsEnabled"] == (False,)
assert all(widgets[name].calls["SetRenderOpacity"] == (theme.OPACITY_DISABLED,) for name in speed_row)
form.shown["walk"] = True
form.refresh_dependency(form.resolve())
change = widgets["command:third_person:keyboard"]
assert change.calls["SetNoKeySpecifiedText"] == ("CHANGE",) and change.calls["SetKeySelectionText"] == ("PRESS A KEY",)
panel_preferences.french.value = True
form.refresh_labels(form.resolve())
assert change.calls["SetNoKeySpecifiedText"] == ("MODIFIER",)
assert change.calls["SetKeySelectionText"] == ("APPUIE SUR UNE TOUCHE",)
assert widgets["value:third_person:keyboard"].calls["SetText"] == ("P",)
assert widgets["value:shoulder:controller"].calls["SetText"] == ("Triangle",)
assert widgets["value:shoulder:controller:icon"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert widgets["setting:shoulder_left_label"].calls["SetText"] == ("DROITE",)
form.shown["shoulder_left"] = True
form.refresh_labels(form.resolve())
assert widgets["setting:shoulder_left_label"].calls["SetText"] == ("GAUCHE",)

# OPTIONS in three tabs (Kevin, 2026-10-06, sketch A): the camera, commands and language pages each carry the
# tilted title and the three tabs, their own lit; the commands and language pages have no sidebar button; the gear
# reopens the last tab seen.
TABS = ("options", "commands", "language")
model.mod.save_settings = lambda: None  # a page is saved as the menu's last one
assert all(f"tab:{page}:{tab}" in widgets for page in TABS for tab in TABS)
hidden = [node for node in Widget.created if node.calls.get("SetVisibility") == ("ESlateVisibility.Collapsed",)]
assert all(any(widgets[f"nav:{page}"] in walk(node) for node in hidden) for page in ("commands", "language"))
assert not any(widgets["nav:dash"] in walk(node) for node in hidden)


def click(name):
    widgets[name].calls["SetIsChecked"] = (True,)
    form.poll()


def shown():
    return widgets["pages"].calls["SetActiveWidgetIndex"][0]


gold = (w.linear(theme.COLOR_GOLD),)
assert model.page == "options" and shown() == len(model.pages)
assert widgets["tab:options:options_fill"].calls["SetBrushColor"] == gold
assert widgets["options_description:options"].calls["SetText"] == ("Vue, visée, caméra orbitale et loot.",)
click("tab:options:commands")
assert model.page == "commands" and shown() == model.pages.index("commands")
assert widgets["tab:commands:commands_label"].calls["SetText"] == ("COMMANDES",)
assert widgets["tab:commands:commands_fill"].calls["SetBrushColor"] == gold
assert widgets["tab:commands:options_fill"].calls["SetBrushColor"] != gold
assert widgets["options_description:commands"].calls["SetText"] == (
    "Touches de la caméra, au clavier et à la manette.",)
assert widgets["options_fill"].calls["SetBrushColor"] == gold, "the gear stays lit on every tab"
click("tab:commands:language")
assert model.page == "language" and shown() == model.pages.index("language")
assert widgets["tab:language:language_label"].calls["SetText"] == ("LANGUES",)
click("nav:dash")
assert model.page == "dash" and shown() == model.pages.index("dash")
assert widgets["options_fill"].calls["SetBrushColor"] != gold
click("options")
assert model.page == "language" and shown() == model.pages.index("language"), "the gear reopens the last tab"
click("tab:language:options")
assert model.page == "options" and shown() == len(model.pages)
# The head stays in reach (Kevin, 2026-10-06): above the scroll area of the cards, never inside it.
cards = {"options": "heading:camera", "commands": "heading:command_tools", "language": "heading:language"}
for page, card in cards.items():
    frame = widgets["pages"].children[len(model.pages) if page == "options" else model.pages.index(page)]
    top, scroll = frame.children
    assert frame.kind == "VerticalBox" and scroll.kind == "ScrollBox", page
    assert widgets[f"options_title:{page}"] in walk(top) and widgets[f"tab:{page}:options"] in walk(top), page
    assert widgets[f"options_description:{page}"] in walk(top), page
    assert widgets[card] in walk(scroll) and widgets[f"options_title:{page}"] not in walk(scroll), page

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
# Three fixed framing cards add 69 entries, the header's size button 5, the DYNAMIC CAMERA tab (its head, its card,
# seven rows and a fourth tab button on every head) about 80; no dynamically growing registry.
assert len(widgets) < 820, "the fixed widget registry must stay bounded"

# Each theme changes colours only, read when the window is drawn: no colour of another theme stays (2026-10-06).
veils = {tuple(theme.HOVER_OVERLAY), tuple(theme.PRESS_OVERLAY)}
original = theme.rgba
for name in theme.THEMES:
    panel_preferences.theme.value = name
    used = []
    theme.rgba = lambda colour, alpha=1.0: used.append((colour, alpha)) or original(colour, alpha)
    try:
        _root, drawn = panel_view.build_view(SimpleNamespace(), model)
        panel_form.PanelForm({key: (lambda item=item: item) for key, item in drawn.items()}, model)
    finally:
        theme.rgba = original
    palette = {**theme._EMBER, **theme.PALETTES[name]}.values()
    stray = {(colour, alpha) for colour, alpha in used if colour not in palette and (colour, alpha) not in veils}
    assert not stray, f"{name}: colours kept from another theme: {sorted(stray)}"
    words = {"EN": {"EMBER": "THEME: EMBER", "DARK": "THEME: DARK", "LIGHT": "THEME: LIGHT", "BL4": "THEME: BL4"},
             "FR": {"EMBER": "THÈME : BRAISE", "DARK": "THÈME : SOMBRE", "LIGHT": "THÈME : CLAIR", "BL4": "THÈME : BL4"}}
    assert drawn["theme_label"].calls["SetText"] == (words[model.language][name],), "the header names the theme"
panel_preferences.theme.value = "EMBER"
result.success()
