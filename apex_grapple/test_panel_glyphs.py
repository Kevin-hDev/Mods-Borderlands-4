"""Native button brushes are read without mutating bindings, tables or game input mode."""

from types import SimpleNamespace as NS
import control_fixture as f
from apex_grapple import panel_glyphs as g, panel_preferences as preferences, panel_model

def table(family):
    entries = [NS(Key=NS(KeyName=f"Gamepad_FaceButton_{side}"), KeyBrush=NS(ResourceObject=object()))
               for side in ("Bottom", "Right", "Left", "Top")]
    return NS(GamepadName=family, InputBrushDataMap=entries)

ps, xbox = table("PS5"), table("XSX")
f.state["by_class"]["CommonInputBaseControllerData"] = [ps, xbox]
reader = g.Catalogue()
assert reader.brush("PS5", "Gamepad_FaceButton_Bottom") is ps.InputBrushDataMap[0].KeyBrush
assert reader.brush("XSX", "Gamepad_FaceButton_Right") is xbox.InputBrushDataMap[1].KeyBrush
assert reader.brush("PS5", "Gamepad_DPad_Down") is None
ps.destroyed = True
assert reader.brush("PS5", "Gamepad_FaceButton_Bottom") is None
assert g.label("Gamepad_FaceButton_Bottom", "PS5", "FR") == "Croix"
assert g.label("Gamepad_FaceButton_Bottom", "XSX", "FR") == "A"
assert g.label("Gamepad_DPad_Down", "PS5", "FR") != "Croix"
assert g.label("ThumbMouseButton2", "PS5", "FR") == "ThumbMouseButton2"
model = panel_model.Model(f.mod)
assert model.controller_icons == "PS5"
before = tuple(o.value for o in f.config.ALL)
assert model.change_controller_icons("XSX") and model.controller_icons == "XSX"
assert tuple(o.value for o in f.config.ALL) == before
f.mod.fail_save = True
assert not model.change_controller_icons("PS5") and model.controller_icons == "XSX"
f.mod.fail_save = False
assert not model.change_controller_icons("invented")
assert model.restore() and model.controller_icons == "XSX"  # Appearance is a preference, like language.
assert preferences.controller_icons in __import__('apex_grapple.menu', fromlist=['MENU']).MENU
ps.destroyed = False
ps.InputBrushDataMap = ps.InputBrushDataMap * (g.MAX_KEYS + 1)
assert reader.brush("PS5", "Gamepad_FaceButton_Bottom") is None
assert reader.brush("unknown", "Gamepad_FaceButton_Bottom") is None
f.state["by_class"]["CommonInputBaseControllerData"] = [xbox] * (g.MAX_TABLES + 1)
assert not g.Catalogue().tables
print("OK | native PS/Xbox brushes, weak lifetime, separate D-pad, labels, preference persistence/rollback")
