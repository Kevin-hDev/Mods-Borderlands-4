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
assert len(model.pages) == 17 and model.pages[-7:] == ("commands", "language", "dynamic_camera", "shoulder", "aiming",
                                                       "sensitivity", "omni_direction")
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
assert widgets["options_description:options"].calls["SetText"] == ("Vue, caméra orbitale et loot.",)
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
# seven rows and a fourth tab button on every head) about 80, the FREE LOOK command card 17, the automatic shoulder's
# three rows 42, the SHOULDER VIEW tab (its head, its card and a fifth tab button on every head) 55 (922 in all on
# 2026-10-07); the camera distance's two rows, the AIMING and SENSITIVITY tabs (their heads, cards and rows, and two
# more tab buttons on every head) bring it to 1110 on 2026-10-08; the five weapon-type bars and their switch to 1149
# the same day; the sniper optic row (six boxes and the slider holding its value), the SNIPER ZOOM command card and five
# optic sensitivity bars to 1239 on 2026-10-09; the OMNI DIRECTION tab (its head, card, four rows, three pop-ups and an
# eighth tab button on every head) to 1450 the same day; the other weapon types' five optic rows and the heavy
# weapons' sensitivity bar to 1584 that evening; no dynamically growing registry.
assert len(widgets) < 1650, "the fixed widget registry must stay bounded"
# Free Look's settings sit on the CAMERA tab; COMMANDS only holds keys (Kevin, 2026-10-07).
free_look = [widgets[f"setting:{key}"] for key in ("free_look", "free_look_keyboard_hold", "free_look_controller_hold",
                                                   "free_look_hold_time")]
assert all(widget in walk(widgets["camera:settings"]) for widget in free_look)
assert not any(widget in walk(widgets["commands:settings"]) for widget in free_look)
# The shoulder's settings sit on their own SHOULDER VIEW tab, the smooth camera transitions stay on CAMERA VIEW
# (Kevin, 2026-10-07).
shoulder = [widgets[f"setting:{key}"] for key in ("shoulder_left", "shoulder_auto", "shoulder_auto_swap",
                                                  "shoulder_auto_return", "shoulder_smooth")]
assert all(widget in walk(widgets["shoulder:settings"]) for widget in shoulder)
assert not any(widget in walk(widgets["camera:settings"]) for widget in shoulder)
assert all(widgets[f"setting:{key}"] in walk(widgets["camera:settings"])
           for key in ("third_person", "orbit_smooth", "shoulder_seconds"))
assert all(f"tab:{page}:shoulder" in widgets for page in ("options", "shoulder", "dynamic_camera", "commands"))
# AIMING holds the aim view and the aim zoom, SENSITIVITY its two settings; neither stays on CAMERA VIEW, and every
# head shows the seven tabs (Kevin, 2026-10-08).
from apex_movement import panel_options  # noqa: E402
assert all(f"tab:{page}:{tab}" in widgets for page in panel_options.TABS for tab in panel_options.TABS)
moved = {"aiming": ("third_person_ads", "camera_framing_zoom"), "sensitivity": ("sensitivity_look", "sensitivity_aim")}
for page, keys in moved.items():
    inside = [widgets[f"setting:{key}"] for key in keys]
    assert all(widget in walk(widgets[f"{page}:settings"]) for widget in inside), page
    assert not any(widget in walk(widgets["camera:settings"]) for widget in inside), page
assert widgets["setting:camera_framing_horizontal"] in walk(widgets["camera:settings"])

# AIMING's optic rows (Kevin, 2026-10-09), one per weapon type in the game's order: BDL4 then the zooms; a zoom
# unticks BDL4, BDL4 unticks every zoom.
from apex_movement import panel_optics  # noqa: E402
OPTIC_ROWS = ("pistol_optics", "smg_optics", "shotgun_optics", "assault_optics", "sniper_optics", "heavy_optics")
aiming = list(walk(widgets["aiming:settings"]))
assert all(widgets[panel_optics.box_name(row, zoom)] in aiming
           for row in OPTIC_ROWS for zoom in panel_optics.boxes(row))
assert [widget for widget in aiming if widget in [widgets[f"setting:{row}"] for row in OPTIC_ROWS]] == [
    widgets[f"setting:{row}"] for row in OPTIC_ROWS]
assert [box for box in widgets if box.startswith("optic:heavy_optics:") and "_" not in box[19:]] == [
    "optic:heavy_optics:bdl4", "optic:heavy_optics:1", "optic:heavy_optics:2"]
# A new install: x1 lit for pistols, BDL4 for heavy weapons, as they aimed before their rows.
assert widgets["optic:pistol_optics:1_fill"].calls["SetBrushColor"] == gold
assert widgets["optic:pistol_optics:bdl4_fill"].calls["SetBrushColor"] != gold
assert widgets["optic:heavy_optics:bdl4_fill"].calls["SetBrushColor"] == gold
form.shown["third_person"] = True
click("optic:sniper_optics:6")
assert form.pending["sniper_optics"] == 8
assert widgets["optic:sniper_optics:6_fill"].calls["SetBrushColor"] == gold
assert widgets["optic:sniper_optics:bdl4_fill"].calls["SetBrushColor"] != gold
click("optic:sniper_optics:bdl4")
assert "sniper_optics" not in form.pending and widgets["optic:sniper_optics:bdl4_fill"].calls["SetBrushColor"] == gold
assert widgets["optic:sniper_optics:6_fill"].calls["SetBrushColor"] != gold
click("optic:pistol_optics:3")
assert form.pending["pistol_optics"] == 0b101 and "sniper_optics" not in form.pending
click("optic:pistol_optics:3")
assert "pistol_optics" not in form.pending
# The « ? » opens a help pop-up over the whole window, never inside a page that could cut it; a click beside it, its
# CLOSE button or Escape close it alone (Kevin: « attention à ce que ça ne ferme pas tout le menu »).
popup = widgets["popup:optics"]
assert popup in walk(widgets["popups"]) and popup not in walk(widgets["pages"])
assert popup.calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
for closer in ("popup:optics:beside", "popup:optics:close", None):
    click("optic:help")
    assert form.popup == "optics" and popup.calls["SetVisibility"] == ("ESlateVisibility.SelfHitTestInvisible",)
    if closer is None:
        assert form.escape() is False, "Escape closes the pop-up, not the window"
    else:
        click(closer)
    assert form.popup is None and popup.calls["SetVisibility"] == ("ESlateVisibility.Collapsed",), closer
assert widgets["heading:popup_optics"].calls["SetText"] == ("OPTIQUES",)
assert widgets["popup:optics:close_label"].calls["SetText"] == ("FERMER",)
# It shows the zoom key as the COMMANDS page does, read again at each opening: a key changed there shows at once.
for device in ("keyboard", "controller"):
    assert (widgets[f"value:optics_help:{device}"].calls["SetText"]
            == widgets[f"value:free_look:{device}"].calls["SetText"]), device
camera_settings.commands.apply({"sniper_zoom_key": "K"})
click("optic:help")
assert widgets["value:optics_help:keyboard"].calls["SetText"] == ("K",)
click("popup:optics:close")
camera_settings.commands.apply(camera_settings.commands.defaults())

# OMNI DIRECTION (Kevin, 2026-10-09): the eighth tab, last on the second row; four rows, two of boxes, three « ? ».
assert panel_options.TAB_ROWS[1][-1] == "omni_direction"
omni_rows = ("omni_body", "omni_angle", "omni_direction_sprint", "omni_crouch")
assert all(widgets[f"setting:{key}"] in walk(widgets["omni_direction:settings"]) for key in omni_rows)
assert not any(widgets[f"setting:{key}"] in walk(widgets["camera:settings"]) for key in omni_rows)
click("tab:options:omni_direction")
assert model.page == "omni_direction" and shown() == model.pages.index("omni_direction")
assert widgets["tab:omni_direction:omni_direction_label"].calls["SetText"] == ("OMNI DIRECTION",)
# The body turns in third person only: its tab says so while third person is off (Kevin, 2026-10-09: a greyed page
# that said nothing).
form.shown["third_person"] = False
form.refresh_labels(form.resolve())
needed = "\nActive la troisième personne dans l'onglet CAMÉRA."
assert all(widgets[f"group:{page}"].calls["SetText"][0].endswith(needed)
           for page in ("aiming", "sensitivity", "omni_direction"))
form.shown["third_person"] = True
form.refresh_labels(form.resolve())
assert widgets["group:omni_direction"].calls["SetText"] == ("Le corps suit ta course, en troisième personne.",)
assert widgets["omni:omni_crouch:1_label"].calls["SetText"] == ("GLISSADE",)
assert widgets["omni:omni_crouch:1_fill"].calls["SetBrushColor"] == gold, "Apex Movement slides by default"
assert widgets["omni:omni_angle:0_label"].calls["SetText"] == ("360°",)
assert widgets["omni:omni_angle:0_fill"].calls["SetBrushColor"] == gold
form.shown["third_person"] = True
click("omni:omni_crouch:0")
assert form.pending["omni_crouch"] == 0 and widgets["omni:omni_crouch:0_fill"].calls["SetBrushColor"] == gold
click("omni:omni_crouch:1")
assert "omni_crouch" not in form.pending
for key, title in (("omni_body", "ORIENTATION DU CORPS"), ("omni_angle", "ANGLE"), ("omni_crouch", "CÔTÉS ET ARRIÈRE")):
    help_popup = widgets[f"popup:{key}"]
    assert help_popup in walk(widgets["popups"]) and help_popup not in walk(widgets["pages"])
    assert widgets[f"omni:{key}:help_label"].calls["SetText"] == ("?",)
    click(f"omni:{key}:help")
    assert form.popup == key and widgets[f"heading:popup_{key}"].calls["SetText"] == (title,)
    assert widgets[f"omni_help:{key}"].calls["SetText"][0].startswith(("En troisième", "360°", "Quand tu sprintes"))
    click(f"popup:{key}:close")
    assert form.popup is None
assert "omni_direction_sprint" in form.model.options and "omni:omni_direction_sprint:help" not in widgets
click("tab:omni_direction:options")

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
