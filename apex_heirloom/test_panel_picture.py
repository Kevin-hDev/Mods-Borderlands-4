"""Tests a page's pictures, one per heirloom (sketch H2): a page without any, or a window with no world, keeps its head
as it was; pictures that do not load, or that their image refuses, leave no empty frame and are written once each;
loaded ones sit right of the head, one over the other at the menu's size, the chosen heirloom's shown and the other
collapsed, a picture that did not load simply absent. Each file ships with the mod, a real PNG under 200 kB, shaped
as the menu sizes it."""

import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

state = heirloom_stubs.install()

import unrealsdk  # noqa: E402

from apex_heirloom import menu, panel_assets, panel_picture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Widget:
    refuse = False

    def __init__(self, kind, owner):
        self.kind, self.children, self.calls = kind, [], {}

    def __getattr__(self, name):
        if name.startswith("Set") or name.startswith("AddChild"):
            return lambda *args: self.call(name, args)
        raise AttributeError(name)

    def call(self, name, args):
        if name == "SetBrushFromTexture" and Widget.refuse:
            raise RuntimeError("refused")
        if name == "SetContent":
            self.children[:] = [args[0]]
        elif name.startswith("AddChild"):
            self.children.append(args[0])
            return Widget("Slot", self)
        self.calls[name] = args


unrealsdk.construct_object = Widget
unrealsdk.find_enum = lambda name: type("Enum", (), {"__getattr__": lambda self, member: member})()
asked: list[tuple] = []
texture = object()
loads = [texture]


def fake_texture(world, name="avatar.png"):
    asked.append((world, name))
    return loads[0]


panel_assets.texture = fake_texture
world = object()

rows, widgets = Widget("VerticalBox", None), {}
choose, pictures = menu.PICTURES["heirloom"]
check("a page without a picture keeps its head as it was, no picture asked",
      panel_picture.head(rows, widgets, "holster", world) is rows and not rows.children and not asked)
check("nor with no world to load it in (the CONTROLS card)",
      panel_picture.head(rows, widgets, "heirloom", None) is rows and not rows.children and not asked)

loads[0] = None
check("pictures that do not load leave no empty frame",
      panel_picture.head(rows, widgets, "heirloom", world) is rows and not rows.children and not widgets
      and asked == [(world, name) for name, _, _ in pictures.values()])

loads[0], Widget.refuse = texture, True
check("nor ones their image refuses, each written once",
      panel_picture.head(rows, widgets, "heirloom", world) is rows and not rows.children and not widgets
      and panel_picture.head(rows, widgets, "heirloom", world) is rows
      and len(state["errors"]) == len(pictures)
      and all(f"picture:heirloom:{choice}" in error for choice, error in zip(pictures, state["errors"])))
Widget.refuse = False

head = panel_picture.head(rows, widgets, "heirloom", world)
line = rows.children[0] if rows.children else None
check("loaded pictures: the head goes left of them, on one line of the card",
      len(rows.children) == 1 and line.kind == "HorizontalBox" and line.children[0] is head
      and head.kind == "VerticalBox")
stack = line.children[1] if line is not None and len(line.children) > 1 else None
check("... the pictures right of it, one over the other, each at the menu's size, its texture on its image",
      stack is not None and stack.kind == "Overlay" and len(stack.children) == len(pictures)
      and all(box is widgets[f"picture_box:heirloom:{choice}"] and box.kind == "SizeBox"
              and box.calls["SetWidthOverride"] == (float(pictures[choice][1]),)
              and box.calls["SetHeightOverride"] == (float(pictures[choice][2]),)
              and box.children == [widgets[f"picture:heirloom:{choice}"]]
              and widgets[f"picture:heirloom:{choice}"].calls["SetBrushFromTexture"] == (texture, False)
              for box, choice in zip(stack.children, pictures)))


def state_of(choice):
    return widgets[f"picture_box:heirloom:{choice}"].calls.get("SetVisibility", (None,))[0]


panel_picture.show(widgets, {"model": "axe"})
check("the axe chosen: its picture shows, the knife's is collapsed",
      state_of("axe") == "HitTestInvisible" and state_of("jakobs_knife") == "Collapsed")
panel_picture.show(widgets, {"model": "sword"})
check("a heirloom no longer offered: the knife's", state_of("jakobs_knife") == "HitTestInvisible"
      and state_of("axe") == "Collapsed")
del widgets["picture_box:heirloom:axe"]
panel_picture.show(widgets, {"model": "axe"})
check("the chosen one did not load: none shows, nothing else asked", state_of("jakobs_knife") == "Collapsed")

for name, width, height in pictures.values():
    data = (HERE / "apex_heirloom" / "assets" / name).read_bytes()
    pixels = struct.unpack(">II", data[16:24])
    check(f"{name} ships with the mod, a real PNG under 200 kB, as the window's files must be",
          data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) < 200_000 and name in panel_assets.NAMES)
    check("... shaped as the menu sizes it, to 1 %",
          abs(pixels[0] / pixels[1] - width / height) < 0.01 * width / height)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
