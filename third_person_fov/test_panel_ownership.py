"""A live menu follows camera ownership when its gameplay switch is toggled."""

import weakref
import panel_fixture as f
from third_person_fov import camera
from apex_camera_runtime import shared, constants

f.mod.disable()
runtime = shared.shared(weak_ref=weakref.ref, address_of=id)
runtime.register("omni_sprint", 100, object(), constants.PROTOCOL)
_, widgets, form = f.build()
print("BEFORE", f.mod.is_enabled, shared.elected(), form.model.camera_elsewhere)
assert form.model.camera_elsewhere
f.click(form, widgets, "enabled")
print("AFTER", f.mod.is_enabled, shared.elected(), form.model.camera_elsewhere)
# Differential checks: registration works; a fresh model detects ownership correctly.
assert f.mod.is_enabled and shared.elected() == "third_person_fov", "Activation or election failed"
assert not camera.elected_elsewhere(), "Camera adapter failed to observe new owner"
assert not form.model.camera_elsewhere, "Open menu retained the old owner"
form.poll()
assert widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
assert widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
assert widgets["commands:external"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert form.model.write({"fov": 128})
assert form.model.restore() and form.model.can_undo
f.click(form, widgets, "enabled")
form.poll()
assert shared.elected() == "omni_sprint" and form.model.camera_elsewhere
assert widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert not form.model.write({"fov": 130}) and not form.model.undo()
assert widgets["undo"].calls["SetIsEnabled"] == (False,), "Dormant camera cannot undo"
runtime.register("apex_movement", 200, object(), constants.PROTOCOL)
f.click(form, widgets, "enabled")
form.poll()
assert shared.elected() == "apex_movement" and form.model.camera_elsewhere
assert widgets["restore"].calls["SetIsEnabled"] == (False,)
runtime.unregister("apex_movement")
form.poll()
assert not form.model.camera_elsewhere
assert widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
shared.reset_for_tests()
print("RESULTAT: TOUS LES TESTS PASSENT")
