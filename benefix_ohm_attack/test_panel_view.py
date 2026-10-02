"""Benefix Ohm Attack's window as built (sketch M1, Kevin, 2026-10-01): the frame of our other mods under this mod's
name, one BEAM page with its two cards, BEAM then ENERGY, the element between two arrows; then the COMMANDS page
(sketch C): one card, a keyboard/mouse row and a controller row, then the icons, the reset and the Esc hint. The
widgets the view registers are those the form reads and those the interaction tests use (panel_fixture.py)."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture  # noqa: E402

import unrealsdk  # noqa: E402

from benefix_ohm_attack import menu, mod, panel_assets, panel_factory, panel_fonts, panel_form, panel_model  # noqa: E402
from benefix_ohm_attack import panel_theme as theme, panel_view, settings  # noqa: E402

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
    """Any widget of the game: remembers its children and what it was told."""

    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner
        self.children, self.slots, self.calls = [], [], {}
        self.Font = Struct()

    def __getattr__(self, name):
        if name.startswith("Set") or name.startswith("AddChild"):
            return lambda *args: self.call(name, args)
        if name.startswith("Get") or name.startswith("Is"):
            return lambda *args: False
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


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
# Neither the avatar nor the fonts' files load in this fake game.
panel_assets.texture = lambda _world, name="avatar.png": None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

model = panel_model.Model(mod)
root, widgets = panel_view.build_view(SimpleNamespace(), model)
check("the view registers exactly the widgets the interaction tests give the form",
      set(widgets) == panel_fixture.names(model))
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
form.poll()
bindings = panel_factory.PanelBindings()
built = panel_factory.build(SimpleNamespace(), bindings, True)
check("the factory opens the window on the mod, switched off included, and hands the form the model",
      bindings.mod is mod and bindings.ready() and bindings.prepare() and isinstance(built[1], panel_form.PanelForm)
      and built[1].model.mod is mod)

check("two pages, BEAM then COMMANDS, opened on BEAM, under the mod's working name",
      theme.PAGES == ("beam", "controls") == menu.SHOWN_PAGES and len(widgets["pages"].children) == 2
      and widgets["focus"] is widgets["nav:beam"] and theme.BRAND == "BENEFIX OHM ATTACK")
check("EN and FR sit in the header", "EN" in widgets and "FR" in widgets)

page = list(walk(widgets["pages"].children[0]))


def place(name):
    return page.index(widgets[name])


order = ["heading:beam", "group:beam", "label:element", "label:damage", "heading:energy", "group:energy",
         "label:show_bar", "label:drain", "label:regen", "label:regen_delay"]
check("the BEAM page holds two cards (sketch M1): BEAM with the element and the damage, then ENERGY with the bar's "
      "switch and the three energy rows", all(widgets[name] in page for name in order)
      and [place(name) for name in order] == sorted(place(name) for name in order))
check("the two cards are apart: no card's frame holds both titles, and each row is in its own card's",
      not any(widgets["heading:beam"] in walk(node) and widgets["heading:energy"] in walk(node)
              for node in page if node.kind == "Border")
      and any(widgets["heading:energy"] in walk(node) and widgets["label:drain"] in walk(node)
              and widgets["label:element"] not in walk(node) for node in page if node.kind == "Border"))
check("every setting has its control, its row and its box, on the BEAM page",
      all(widgets[f"{part}:{key}"] in page for key in model.options for part in ("setting", "row", "block")))
check("each row sits in its own box with its description",
      all(widgets[name] in walk(widgets[f"block:{key}"]) for key in model.options
          for name in (f"row:{key}", f"description:{key}")))
check("the element is two arrows around its name, its place among the elements in the value box",
      all(widgets[name] in walk(widgets["setting:element"])
          for name in ("setting:element:previous", "choice:element", "setting:element:next"))
      and widgets["value:element"] in walk(widgets["row:element"])
      and widgets["value:element"] not in walk(widgets["setting:element"]))
check("the bar's switch is a button, the four numbers are sliders with their value boxes",
      widgets["setting:show_bar"].kind == "CheckBox"
      and all(widgets[f"setting:{key}"].kind == "Slider" and f"value:{key}" in widgets and f"fill:{key}" in widgets
              for key in ("damage", "drain", "regen", "regen_delay")))
check("each slider has its setting's bounds and step",
      all(widgets[f"setting:{option.identifier}"].calls["SetMinValue"] == (float(option.min_value),)
          and widgets[f"setting:{option.identifier}"].calls["SetMaxValue"] == (float(option.max_value),)
          and widgets[f"setting:{option.identifier}"].calls["SetStepSize"] == (float(option.step),)
          for option in (settings.damage, settings.drain, settings.regen, settings.regen_delay)))

commands = list(walk(widgets["pages"].children[1]))
card = widgets["card:command_fire"]
check("the COMMANDS page: the FIRE card, then the icons, the reset, its status and the Esc hint",
      card in commands and commands.index(card) < commands.index(widgets["icons:PS5"])
      < commands.index(widgets["commands_reset"]) < commands.index(widgets["commands_status"])
      < commands.index(widgets["escape_hint"]))
check("the card holds its title, its sentence, then a keyboard/mouse row and a controller row",
      all(widgets[f"{part}:command_fire"] in walk(card) for part in ("heading", "group"))
      and all(widgets[f"{part}:fire:{device}"] in walk(card) for device in ("keyboard", "controller")
              for part in ("device", "command", "clear", "value")))
check("the keyboard's row ignores the controller's buttons, the controller's row takes them",
      widgets["command:fire:keyboard"].calls["SetAllowGamepadKeys"] == (False,)
      and widgets["command:fire:controller"].calls["SetAllowGamepadKeys"] == (True,))
check("no picture and no sentence in an orange frame: this mod has none",
      not any(name.startswith(("picture", "notice:")) for name in widgets))
check("every widget is attached once", attached_once(root, widgets))

check("the form writes each card's name and sentence, the second card's from the mod's words",
      widgets["heading:beam"].calls["SetText"] == ("BEAM",) and widgets["heading:energy"].calls["SetText"] == ("ENERGY",)
      and widgets["group:energy"].calls["SetText"][0].startswith("The beam has its own energy")
      and widgets["group:beam"].calls["SetText"][0].startswith("Hold the beam's key"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
