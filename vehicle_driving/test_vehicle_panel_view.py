"""The full Vehicle Driving window builds both pages in Grapple's approved frame."""

from types import SimpleNamespace

import sdk_stubs

sdk_stubs.install()

import unrealsdk  # noqa: E402

from vehicle_driving import panel_assets, panel_fonts, panel_model, panel_theme as theme, panel_view  # noqa: E402
from vehicle_driving import panel_preferences  # noqa: E402


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

model = panel_model.Model(SimpleNamespace(is_enabled=True))
root, widgets = panel_view.build_view(SimpleNamespace(), model)
assert root.kind == "UserWidget"
# The window sits on a clear layer over the whole screen (panel_modal, 2026-10-06).
assert (root.WidgetTree.RootWidget.kind == "CanvasPanel"
        and [child.kind for child in root.WidgetTree.RootWidget.children] == ["BackgroundBlur", "ScaleBox"])
assert len(widgets["pages"].children) == len(model.pages) == 6
assert widgets["focus"] is widgets["nav:driving"]
assert theme.BRAND == "VEHICLE DRIVING"

attached = set()


def visit(node):
    assert id(node) not in attached, "a widget is attached twice"
    attached.add(id(node))
    for child in node.children:
        visit(child)


visit(root.WidgetTree.RootWidget)
assert all(id(widget) in attached for widget in widgets.values())
assert sum(node.kind == "ScrollBox" for node in Widget.created) == len(model.pages) + 1
assert all(f"setting:{key}" in widgets for key in model.options)
assert len(widgets) < 450, "each widget is resolved during every menu poll"


def order(node, found):
    found.append(node)
    for child in node.children:
        order(child, found)
    return found


# The CAMERA page (Kevin, 2026-10-06): the view's arrows and the Custom sliders, then the key's card, then the icons,
# the keys' reset and the Esc hint, in this order on its one page.
camera = order(widgets["pages"].children[model.pages.index("camera")], [])
parts = ("heading:camera", "setting:vehicle_view:previous", "setting:vehicle_view:next", "setting:custom_height",
         "heading:command_view", "command:view:keyboard", "clear:view:keyboard", "command:view:controller",
         "icons:PS5", "commands_reset", "commands_status", "escape_hint")
assert all(widgets[name] in camera for name in parts), "every part of the CAMERA page is on it"
assert [camera.index(widgets[name]) for name in parts] == sorted(camera.index(widgets[name]) for name in parts)
assert widgets["command:view:keyboard"].calls["SetAllowGamepadKeys"] == (False,)
assert widgets["command:view:controller"].calls["SetAllowGamepadKeys"] == (True,)
assert not any(widgets[name] in camera for name in ("heading:driving", "setting:max_speed"))

# Each theme changes colours only, read when the window is drawn: no colour of another theme stays (2026-10-06).
veils = {tuple(theme.HOVER_OVERLAY), tuple(theme.PRESS_OVERLAY)}
original_rgba = theme.rgba
for theme_name in theme.THEMES:
    panel_preferences.theme.value = theme_name
    used = []
    theme.rgba = lambda colour, alpha=1.0: used.append((colour, alpha)) or original_rgba(colour, alpha)
    try:
        panel_view.build_view(SimpleNamespace(), model)
    finally:
        theme.rgba = original_rgba
    allowed = {*{**theme._EMBER, **theme.PALETTES[theme_name]}.values()}
    stray = {(colour, alpha) for colour, alpha in used if colour not in allowed and (colour, alpha) not in veils}
    assert not stray, f"{theme_name}: colours kept from another theme: {sorted(stray)}"
panel_preferences.theme.value = "EMBER"
print("OK | full Vehicle Driving window builds six pages and a scrolling sidebar")
print("RESULTAT: TOUS LES TESTS PASSENT")
