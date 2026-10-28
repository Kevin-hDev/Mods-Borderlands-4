"""Controller images replace positional words while the native selector owns capture."""

from types import SimpleNamespace as NS
import panel_fixture as pf
from apex_grapple import panel_preferences, panel_theme

resource = object()
def make_table(family):
    return NS(GamepadName=family, InputBrushDataMap=[
        NS(Key=NS(KeyName="Gamepad_FaceButton_Bottom"), KeyBrush=NS(ResourceObject=resource)),
        NS(Key=NS(KeyName="Gamepad_FaceButton_Top"), KeyBrush=NS(ResourceObject=resource))])
pf.f.state["by_class"]["CommonInputBaseControllerData"] = [make_table("PS5"), make_table("XSX")]
w, form = pf.create()
w["nav:controls"].checked = True
form.poll()
w["first"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Bottom"
form.poll()
assert w["first"].text_visibility == "Collapsed"
assert w["first:icon"].visibility == "HitTestInvisible"
assert w["first:icon"].icon_brush.ResourceObject is resource
assert w["pad_summary"].visibility == "HitTestInvisible"
assert "Controller :" not in w["current"].text  # Shown by the image row, not duplicated.
saved = pf.f.mod.saved
w["first"].selecting = True
form.poll()
assert w["first"].text_visibility == "Visible"
assert w["first:icon"].visibility == "Collapsed"
assert pf.f.mod.saved == saved
w["first"].selecting = False
w["icons:XSX"].checked = True
form.poll()
assert panel_preferences.controller_icons.value == "XSX"
assert pf.f.config.DEVICES[1].selection() == ("Gamepad_FaceButton_Bottom",)
# Both icons in a chord; turning the second slot off clears its stale image.
w["two"].checked = True
form.poll()
w["first"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Bottom"
w["second"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
assert w["pad_second_box"].visibility == "HitTestInvisible"
assert w["pad_separator"].text == "+"
w["two"].checked = False
form.poll()
assert w["second:icon"].visibility == "Collapsed"
assert w["second"].text_visibility == "Visible"
# Missing native resources use proper button names, without breaking capture.
form.key_display.catalogue.tables.clear()
form.key_display.previous.clear()
w["first"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Bottom"
form.poll()
assert w["first:key_label"].text == "A"
assert w["first:key_label"].visibility == "HitTestInvisible"
print("OK | selector icons, capture hint, saved summary, chord, family choice and missing-resource fallback")
