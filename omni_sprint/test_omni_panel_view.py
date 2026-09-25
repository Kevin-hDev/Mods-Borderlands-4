"""Omni Sprint's window: its sprint and camera pages, or one accurate notice while another camera mod owns them."""

import pathlib
import sys
import weakref
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import unrealsdk  # noqa: E402
from apex_camera_runtime import constants, shared as runtime  # noqa: E402

from omni_sprint import panel_assets, panel_fonts, panel_form, panel_model, panel_preferences  # noqa: E402
from omni_sprint import panel_theme as theme, panel_view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


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


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def attached_once(root, widgets):
    seen = set()
    for node in walk(root.WidgetTree.RootWidget):
        if id(node) in seen:
            return False
        seen.add(id(node))
    return all(id(widget) in seen for widget in widgets.values())


def build():
    Widget.created.clear()
    model = panel_model.Model(SimpleNamespace(is_enabled=True))
    root, widgets = panel_view.build_view(SimpleNamespace(), model)
    form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
    return model, root, widgets, form


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
panel_assets.texture = lambda _world: None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

model, root, widgets, form = build()
check("two pages, opened on OMNI SPRINT, under the mod's name",
      len(widgets["pages"].children) == len(model.pages) == 2 and widgets["focus"] is widgets["nav:omni_sprint"]
      and theme.BRAND == "OMNI SPRINT")
check("EN and FR sit in the header, with no gear nor Options page",
      "EN" in widgets and "FR" in widgets and "options" not in widgets and "language:EN" not in widgets)
check("the page's rows are the camera settings, the FOV row registered to be greyed",
      all(f"row:{key}" in widgets for key in ("third_person", "custom_fov", "fov"))
      and all(f"setting:{key}" in widgets for key in model.options))
row = widgets["row:third_person"]
shown, change = widgets["key:third_person_key"], widgets["setting:third_person_key"]
check("the key and its Change button follow the Third Person switch, with no row of their own",
      "row:third_person_key" not in widgets and "label:third_person_key" not in widgets and len(row.children) == 4
      and shown in walk(row.children[2]) and change in walk(row.children[3])
      and shown.calls["SetVisibility"] == ("ESlateVisibility.HitTestInvisible",))
check("the key field names the saved key, and both fields speak the menu's language",
      shown.calls["SetSelectedKey"][0].Key.KeyName == "P" and change.calls["SetNoKeySpecifiedText"] == ("CHANGE",)
      and change.calls["SetKeySelectionText"] == ("PRESS A KEY",) and shown.calls["SetNoKeySpecifiedText"] == ("NONE",))
check("the sprint's page holds its switch, and each card says what its page sets",
      "row:omni_sprint" in widgets and widgets["label:omni_sprint"].calls["SetText"] == ("SPRINT IN ALL DIRECTIONS",)
      and widgets["group:omni_sprint"].calls["SetText"] == ("The game's sprint, in every direction.",)
      and widgets["group:camera"].calls["SetText"] == ("View and field of view.",))
panel_preferences.french.value = True
form.refresh_labels(form.resolve())
check("in French, the fields say MODIFIER, APPUIE SUR UNE TOUCHE and AUCUNE",
      change.calls["SetNoKeySpecifiedText"] == ("MODIFIER",)
      and change.calls["SetKeySelectionText"] == ("APPUIE SUR UNE TOUCHE",)
      and shown.calls["SetNoKeySpecifiedText"] == ("AUCUNE",))
check("every widget is attached once", attached_once(root, widgets))
check("one scroll area per page, one for the sidebar",
      sum(node.kind == "ScrollBox" for node in Widget.created) == len(model.pages) + 1)

shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
shared.register("third_person_fov", 300, object(), constants.PROTOCOL)
model, root, widgets, form = build()
check("while another camera mod is on, the camera page holds no setting and the sprint's switch stays",
      not any(setting in name for name in widgets for setting in ("third_person", "fov"))
      and all(name in widgets for name in ("label:omni_sprint", "setting:omni_sprint", "row:omni_sprint")))
check("the camera card does not falsely name Apex Movement when the mini pack owns the camera",
      widgets["group:camera"].calls["SetText"] ==
      ("Un autre mod contrôle la caméra : règle-la dans son menu.",)
      and widgets["group:omni_sprint"].calls["SetText"] == ("Le sprint du jeu, dans toutes les directions.",)
      and attached_once(root, widgets))
runtime.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
