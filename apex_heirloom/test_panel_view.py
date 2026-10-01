"""Apex Heirloom's window as built: Apex Grapple's frame, the HEIRLOOM page with its sentence at the top, the chosen
heirloom's picture beside it (sketch H2), the mode's and the heirloom's buttons, the skin's arrows, each row in a box
the page can hide; the HOLSTER page, then Apex Movement's COMMANDS page (sketch I1): a card per command, PUT AWAY then
INSPECT, each a keyboard/mouse row and a controller row, then an untitled card with the icons, the reset and the Esc
hint."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

import unrealsdk  # noqa: E402

from apex_heirloom import menu, mod, panel_assets, panel_factory, panel_fonts, panel_form, panel_model  # noqa: E402
from apex_heirloom import panel_theme as theme, panel_view  # noqa: E402

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
# The avatar does not load in this fake game; the heirlooms' pictures do.
textures = {"knife.png": object(), "axe.png": object()}
panel_assets.texture = lambda _world, name="avatar.png": textures.get(name)
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

Widget.created.clear()
model = panel_model.Model(mod)
root, widgets = panel_view.build_view(SimpleNamespace(), model)
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
bindings = panel_factory.PanelBindings()
built = panel_factory.build(SimpleNamespace(), bindings, True)
check("the factory, Movement's, opens the window on the mod, the disabled mod included, and hands the form the model",
      bindings.mod is mod and bindings.ready() and bindings.prepare() and isinstance(built[1], panel_form.PanelForm)
      and built[1].model.mod is mod)

check("three pages, HEIRLOOM, HOLSTER then CONTROLS, opened on HEIRLOOM, under the mod's name",
      theme.PAGES == ("heirloom", "holster", "controls") and len(widgets["pages"].children) == 3
      and widgets["focus"] is widgets["nav:heirloom"] and "nav:controls" in widgets and theme.BRAND == "APEX HEIRLOOM")
check("EN and FR sit in the header, as in Grapple's window", "EN" in widgets and "FR" in widgets
      and "options" not in widgets)
heirloom_page = list(walk(widgets["pages"].children[0]))
check("the HEIRLOOM page says the next weapon change applies its settings, above its rows",
      widgets["notice:heirloom"] in heirloom_page
      and heirloom_page.index(widgets["notice:heirloom"]) < heirloom_page.index(widgets["label:heirloom"]))
check("its mode is a button per choice, side by side on the mode's row",
      all(widgets[f"setting:mode:{choice}"] in walk(widgets["setting:mode"]) for choice in ("Apex", "Borderlands"))
      and widgets["setting:mode"] in heirloom_page)
check("every setting has its control and a row that can be greyed",
      all(f"setting:{key}" in widgets and f"row:{key}" in widgets for key in model.options))
check("each row of a page, rule and description included, in a box of its own that the page can hide",
      all(widgets[name] in walk(widgets[f"block:{key}"]) for key in model.options
          for name in (f"row:{key}", f"description:{key}")))
check("the heirloom is a button per heirloom; the skin, two arrows around its name, its place in the value box",
      all(widgets[f"setting:model:{name}"] in walk(widgets["setting:model"]) for name in ("jakobs_knife", "axe"))
      and all(widgets[name] in walk(widgets["setting:skin_axe"])
              for name in ("setting:skin_axe:previous", "choice:skin_axe", "setting:skin_axe:next"))
      and widgets["value:skin_axe"] in walk(widgets["row:skin_axe"])
      and widgets["value:skin_axe"] not in walk(widgets["setting:skin_axe"]))
commands = list(walk(widgets["pages"].children[2]))
cards = [widgets["card:command_put_away"], widgets["card:command_inspect"]]
check("the COMMANDS page: the PUT AWAY card, then INSPECT, then the icons, the reset, its status and the Esc hint",
      all(card in commands for card in cards) and commands.index(cards[0]) < commands.index(cards[1])
      < commands.index(widgets["icons:PS5"]) < commands.index(widgets["commands_reset"])
      < commands.index(widgets["commands_status"]) < commands.index(widgets["escape_hint"]))
check("each card holds its title, its description, then a keyboard/mouse row and a controller row",
      all(widgets[f"{part}:command_{name}"] in walk(widgets[f"card:command_{name}"])
          for name in ("put_away", "inspect") for part in ("heading", "group"))
      and all(widgets[f"{part}:{name}:{device}"] in walk(widgets[f"card:command_{name}"])
              for name in ("put_away", "inspect") for device in ("keyboard", "controller")
              for part in ("device", "command", "clear", "value")))
check("the last card has no title (sketch I1): only the two commands have one",
      sorted(name for name in widgets if name.startswith("heading:command"))
      == ["heading:command_inspect", "heading:command_put_away"]
      and not any(widgets["icons:PS5"] in walk(card) for card in cards))
check("the keyboard's rows ignore the controller's buttons, the controller's rows take them",
      all(widgets[f"command:{name}:keyboard"].calls["SetAllowGamepadKeys"] == (False,)
          and widgets[f"command:{name}:controller"].calls["SetAllowGamepadKeys"] == (True,)
          for name in ("put_away", "inspect")))
check("no key selector from Grapple's CONTROLS page is left", "first" not in widgets and "second" not in widgets
      and "controls_keys" not in widgets and "current" not in widgets)
check("every widget is attached once", attached_once(root, widgets))

picture = widgets.get("picture:heirloom:jakobs_knife")
beside = next((node for node in heirloom_page if node.kind == "HorizontalBox" and picture in walk(node)), None)
check("the HEIRLOOM page shows the knife, chosen, to the right of its title, description and sentence",
      picture is not None and beside is not None and len(beside.children) == 2
      and all(widgets[name] in walk(beside.children[0]) for name in ("heading:heirloom", "group:heirloom",
                                                                      "notice:heirloom"))
      and beside.children[1].kind == "Overlay"
      and widgets["picture_box:heirloom:jakobs_knife"].children == [picture]
      and picture.calls["SetBrushFromTexture"] == (textures["knife.png"], False)
      and widgets["picture_box:heirloom:jakobs_knife"].calls.get("SetVisibility")
      == ("ESlateVisibility.HitTestInvisible",))
check("... the axe's over it, collapsed while the knife is chosen",
      beside is not None and len(beside.children) == 2
      and widgets["picture:heirloom:axe"].calls["SetBrushFromTexture"] == (textures["axe.png"], False)
      and widgets["picture_box:heirloom:axe"] in beside.children[1].children
      and widgets["picture_box:heirloom:axe"].calls.get("SetVisibility") == ("ESlateVisibility.Collapsed",))
check("... each at the size the menu gives it", all(
      widgets[f"picture_box:heirloom:{name}"].calls.get("SetWidthOverride") == (266.0,)
      and widgets[f"picture_box:heirloom:{name}"].calls.get("SetHeightOverride") == (130.0,)
      for name in ("jakobs_knife", "axe")))
check("the other pages show no picture", sorted(name for name in widgets if name.startswith("picture"))
      == ["picture:heirloom:axe", "picture:heirloom:jakobs_knife", "picture_box:heirloom:axe",
          "picture_box:heirloom:jakobs_knife"])

sidebar = next(node for node in walk(root.WidgetTree.RootWidget) if widgets["settings_caption"] in node.children)


def collapsed(page):
    """The sidebar entry holding a page's button, collapsed as a whole."""
    entry = next(child for child in sidebar.children if widgets[f"nav:{page}"] in walk(child))
    return entry.calls.get("SetVisibility") == ("ESlateVisibility.Collapsed",)


check("the full mod offers its three pages", not any(collapsed(page) for page in theme.PAGES))

# Tidy Weapons, a separate file running the holster alone (pack.py): every page is built, its own offered.
full_pages = menu.SHOWN_PAGES
menu.SHOWN_PAGES = ("holster", "controls")
root, widgets = panel_view.build_view(SimpleNamespace(), model)
sidebar = next(node for node in walk(root.WidgetTree.RootWidget) if widgets["settings_caption"] in node.children)
check("a separate file builds every page and collapses the other part's button, which stays in the window",
      len(widgets["pages"].children) == 3 and collapsed("heirloom") and not collapsed("holster")
      and not collapsed("controls") and attached_once(root, widgets))
check("... and opens on its own first page", widgets["focus"] is widgets["nav:holster"])
menu.SHOWN_PAGES = full_pages

textures.clear()
root, widgets = panel_view.build_view(SimpleNamespace(), model)
page = list(walk(widgets["pages"].children[0]))
check("pictures that do not load leave no empty frame: the page as before",
      not any(name.startswith("picture") for name in widgets) and widgets["notice:heirloom"] in page
      and not any(node.kind == "HorizontalBox" and widgets["heading:heirloom"] in walk(node) for node in page)
      and attached_once(root, widgets))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
