"""Current controls reflect saved custom keys and actual game mappings, in both languages."""

from types import SimpleNamespace as NS
import panel_fixture as pf
from sdk_objects import mapping
from apex_grapple import panel_labels, panel_preferences

pf.f.state["extra_classes"]["InputSettings"] = NS(ClassDefaultObject=NS(ConsoleKeys=[NS(KeyName="Tilde")]))
pf.f.state["pc"] = NS(PlayerInput=NS(EnhancedActionMappings=pf.f.state["mappings"]))
w, form = pf.create()
assert "V" in w["current"].text and "R3" in w["current"].text
assert "Current bindings" in w["current"].text
assert form.bindings.save(("ThumbMouseButton2",))[0]
assert form.bindings.save(("Gamepad_LeftShoulder", "Gamepad_RightShoulder"))[0]
saved = pf.f.mod.saved
w, form = pf.create()
assert "ThumbMouseButton2" in w["current"].text
assert "L1 + R1" in w["current"].text
assert pf.f.mod.saved == saved  # Merely displaying bindings never saves them again.
assert form.bindings.reset()[0]
pf.f.state["pc"].PlayerInput.EnhancedActionMappings = [mapping("Action_Melee", "J")]
summary = panel_labels.controls_summary(form.bindings, "FR")
assert "Touches actuelles" in summary and "Clavier / souris : J" in summary
assert "R3" not in summary  # Never invent default keys when the mapping is absent.
pf.f.state["pc"] = None
assert "disponibles en partie" in panel_labels.controls_summary(form.bindings, "FR")

# A refused console key clears the capture draft; the actual binding stays visible.
pf.f.state["extra_classes"]["InputSettings"].ClassDefaultObject.ConsoleKeys = [NS(KeyName="G")]
assert form.bindings.save(("V",))[0]
panel_preferences.language.value = "FR"
w["nav:controls"].checked = True
form.poll()
w["first"].SelectedKey.Key.KeyName = "G"
saved = pf.f.mod.saved
form.poll()
assert "réservée" in w["status"].text
assert w["first"].SelectedKey.Key.KeyName == "None"
assert "Clavier / souris : V" in w["current"].text
for _ in range(3):
    form.poll()
assert pf.f.mod.saved == saved
print("OK | visible current bindings, defaults, reopen, EN/FR, no pawn, console rejection")
