"""A failed image assignment falls back to button names without losing the saved controls."""

import panel_fixture as pf
from types import SimpleNamespace as NS


def fail(*args):
    raise RuntimeError("native image rejected")


table = NS(GamepadName="PS5", InputBrushDataMap=[NS(
    Key=NS(KeyName="Gamepad_FaceButton_Bottom"), KeyBrush=NS(ResourceObject=object()))])
pf.f.state["by_class"]["CommonInputBaseControllerData"] = [table]
w, form = pf.create()
w["nav:controls"].checked = True
form.poll()
w["first:icon"].SetBrush = fail
w["first"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Bottom"
assert not form.poll()
assert w["first:icon"].visibility == "Collapsed"
assert w["first:key_label"].text == "Cross"
assert pf.f.config.DEVICES[1].selection() == ("Gamepad_FaceButton_Bottom",)
saved = pf.f.mod.saved
assert not form.poll() and pf.f.mod.saved == saved
w["first"].selecting = True
assert not form.poll() and w["first"].text_visibility == "Visible"

w, form = pf.create()
w["pad_first"].SetBrush = fail
form.key_display.summary(form, w)
assert w["pad_summary"].visibility == "Collapsed"
assert "Cross" in w["current"].text
print("OK | icon errors keep menu, capture, saved key and readable current controls")
