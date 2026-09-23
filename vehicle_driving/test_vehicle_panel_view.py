"""The full Vehicle Driving window builds both pages in Grapple's approved frame."""

from types import SimpleNamespace

import sdk_stubs

sdk_stubs.install()

import unrealsdk  # noqa: E402

from vehicle_driving import panel_assets, panel_fonts, panel_model, panel_theme as theme, panel_view  # noqa: E402


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
assert root.WidgetTree.RootWidget.kind == "ScaleBox"
assert len(widgets["pages"].children) == len(model.pages) == 2
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
print("OK | full Vehicle Driving window builds both pages and a scrolling sidebar")
print("RESULTAT: TOUS LES TESTS PASSENT")
