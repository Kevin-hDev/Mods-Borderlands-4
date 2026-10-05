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
        self.checked = self.selecting = False
        self.value = 0.0
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
        return self.checked

    def GetValue(self):
        return self.value

    def GetIsSelectingKey(self):
        return self.selecting


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
check("three pages, opened on OMNI SPRINT, under the mod's name",
      len(widgets["pages"].children) == len(model.pages) == 3 and widgets["focus"] is widgets["nav:omni_sprint"]
      and theme.BRAND == "OMNI SPRINT")
check("EN and FR sit in the header, with no gear nor Options page",
      "EN" in widgets and "FR" in widgets and "options" not in widgets and "language:EN" not in widgets)
check("the page's rows are the camera settings, the FOV row registered to be greyed",
      all(f"row:{key}" in widgets for key in
          ("third_person", "shoulder_left", "orbit", "custom_fov", "fov"))
      and all(f"setting:{key}" in widgets for key in model.options))
camera_actions = ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out")
check("camera shortcuts have five cards and one row per device",
      all(f"heading:command_{action}" in widgets for action in camera_actions)
      and all(f"command:{action}:{device}" in widgets
              for action in camera_actions for device in ("keyboard", "controller"))
      and all(f"setting:{key}" not in widgets for key in
              ("third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
               "orbit_key", "orbit_controller", "zoom_in_key", "zoom_in_controller",
               "zoom_out_key", "zoom_out_controller")))
change = widgets["command:third_person:keyboard"]
check("the command selector and current value speak the menu's language",
      change.calls["SetNoKeySpecifiedText"] == ("CHANGE",)
      and change.calls["SetKeySelectionText"] == ("PRESS A KEY",)
      and widgets["value:third_person:keyboard"].calls["SetText"] == ("P",))
form.page = model.pages.index("commands")
duplicate = widgets["command:orbit:keyboard"]
duplicate.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="P"))
form.poll()
check("the real Omni form keeps the key after a refused duplicate",
      model.command_options["orbit_key"].value == "Seven")
check("the real Omni form classifies a refused duplicate",
      form.command_form.notice == "refused")
check("the real Omni form explains a refused duplicate",
      widgets["commands_status"].calls["SetText"] ==
      ("Assignment refused. This input is reserved or already used.",))
check("the sprint's page holds its switch, and each card says what its page sets",
      "row:omni_sprint" in widgets and widgets["label:omni_sprint"].calls["SetText"] == ("SPRINT IN ALL DIRECTIONS",)
      and widgets["group:omni_sprint"].calls["SetText"] == ("The game's sprint, in every direction.",)
      and widgets["group:camera"].calls["SetText"] == ("View, field of view and loot.",))
check("the shoulder uses side labels instead of generic on/off",
      widgets["setting:shoulder_left_label"].calls["SetText"] == ("RIGHT",))
panel_preferences.french.value = True
form.refresh_labels(form.resolve())
check("in French, the fields say MODIFIER, APPUIE SUR UNE TOUCHE and AUCUNE",
      change.calls["SetNoKeySpecifiedText"] == ("MODIFIER",)
      and change.calls["SetKeySelectionText"] == ("APPUIE SUR UNE TOUCHE",)
      and widgets["clear:third_person:keyboard_label"].calls["SetText"] == ("AUCUNE",))
check("the French shoulder side is explicit",
      widgets["setting:shoulder_left_label"].calls["SetText"] == ("DROITE",))
check("every widget is attached once", attached_once(root, widgets))
check("one scroll area per page, one for the sidebar",
      sum(node.kind == "ScrollBox" for node in Widget.created) == len(model.pages) + 1)

shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
shared.register("third_person_fov", 150, object(), constants.PROTOCOL)
model, root, widgets, form = build()
check("while another camera mod is on, stable camera controls are hidden and the sprint's switch stays",
      all(name in widgets for name in
          ("setting:third_person", "setting:shoulder_left", "setting:orbit", "setting:fov",
           "label:omni_sprint", "setting:omni_sprint", "row:omni_sprint", "heading:command_external",
           "command:third_person:keyboard"))
      and widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
      and widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",))
check("the camera card identifies an external owner when Apex Movement wins",
      widgets["group:camera"].calls["SetText"] ==
      ("Un autre mod contrôle la caméra. Règle-la dans son menu.",)
      and widgets["group:omni_sprint"].calls["SetText"] == ("Le sprint du jeu, dans toutes les directions.",)
      and attached_once(root, widgets))
runtime.reset_for_tests()

shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("omni_sprint", 100, object(), constants.PROTOCOL)
model, root, widgets, form = build()
pending_sprint = not model.options["omni_sprint"].value
form.pending["omni_sprint"] = pending_sprint
form.shown["omni_sprint"] = pending_sprint
form.pending["fov"] = 120
form.shown["fov"] = 120
form.changed_at = 10**30  # Keep this draft pending while ownership changes in this poll.
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
form.poll()
check("an open Omni window hides the dormant camera and keeps sprint restoration available",
      model.camera_elsewhere
      and widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
      and widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
      and widgets["commands:external"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
      and widgets["restore"].calls.get("SetIsEnabled") == (True,))
check("a live camera ownership change keeps an unsaved Omni Sprint choice",
      form.pending.get("omni_sprint") is pending_sprint and form.shown["omni_sprint"] is pending_sprint)
check("discarded camera drafts are explained in the open window",
      "fov" not in form.pending and form.notice == "camera_draft_discarded"
      and widgets["notice"].calls["SetText"] ==
      ("Mod caméra changé : les réglages caméra non enregistrés ont été annulés.",))
shared.unregister("apex_movement")
form.poll()
check("the same Omni window restores camera controls when ownership returns",
      not model.camera_elsewhere
      and widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
      and widgets["restore"].calls["SetIsEnabled"] == (True,))
runtime.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
