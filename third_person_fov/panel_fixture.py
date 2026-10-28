"""UMG boundary doubles for real view/form tests; not evidence of in-game rendering."""

from types import SimpleNamespace as NS

import sdk_stubs

state = sdk_stubs.install()

import unrealsdk
from third_person_fov import mod, panel_assets, panel_fonts, panel_model, panel_form, panel_view


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

    def __getattr__(self, name):
        return f"{self.name}.{name}"


class Widget:
    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner
        self.children, self.calls = [], {}
        self.checked = self.selecting = False
        self.value = 0.0
        self.Font = Struct()
        self.SelectedKey = NS(Key=NS(KeyName="None"))

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
            return Widget("Slot", self)
        elif name == "SetIsChecked":
            self.checked = args[0]
        elif name == "SetValue":
            self.value = args[0]
        elif name == "SetSelectedKey":
            self.SelectedKey = args[0]
        self.calls[name] = args

    def IsChecked(self):
        return self.checked

    def GetValue(self):
        return self.value

    def GetIsSelectingKey(self):
        return self.selecting


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def build():
    model = panel_model.Model(mod)
    root, widgets = panel_view.build_view(NS(), model)
    refs = {key: (lambda item=item: item) for key, item in widgets.items()}
    form = panel_form.PanelForm(refs, model)
    return root, widgets, form


def click(form, widgets, key):
    widgets[key].SetIsChecked(True)
    return form.poll()


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
unrealsdk.make_struct = lambda _name, **kwargs: NS(**kwargs)
unrealsdk.find_all = lambda *_args, **_kwargs: []
panel_assets.texture = lambda _world: None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
