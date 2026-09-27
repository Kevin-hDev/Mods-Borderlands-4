"""Build and operate the full camera window, including reopens and controller icon fallback."""

from types import SimpleNamespace as NS
import weakref

import panel_fixture as f
from third_person_fov import panel_preferences as prefs, settings
from apex_camera_runtime import shared, constants

root, widgets, form = f.build()
assert len(widgets["pages"].children) == 2
assert widgets["focus"] is widgets["nav:camera"]
assert "EN" in widgets and "FR" in widgets and "options" not in widgets
assert all(f"row:{key}" in widgets for key in ("third_person", "shoulder_left", "orbit", "fov", "extended_loot", "loot_reach"))
assert "row:custom_fov" not in widgets and "SetIsEnabled" not in widgets["setting:fov"].calls, "the FOV has no switch"
# The shoulder and the orbit camera wait for third person, the loot reach for its switch (review, 2026-09-26).
assert all(widgets[f"setting:{key}"].calls["SetIsEnabled"] == (False,) for key in ("shoulder_left", "orbit"))
assert widgets["setting:loot_reach"].calls["SetIsEnabled"] == (True,)
f.click(form, widgets, "setting:third_person")
assert all(widgets[f"setting:{key}"].calls["SetIsEnabled"] == (True,) for key in ("shoulder_left", "orbit"))
f.click(form, widgets, "setting:extended_loot")
assert widgets["setting:loot_reach"].calls["SetIsEnabled"] == (False,)
f.click(form, widgets, "setting:third_person")
f.click(form, widgets, "setting:extended_loot")
assert not form.pending and widgets["setting:orbit"].calls["SetIsEnabled"] == (False,)
nodes = list(f.walk(root.WidgetTree.RootWidget))
assert len({id(node) for node in nodes}) == len(nodes), "Widget has multiple parents"
assert all(id(widget) in {id(node) for node in nodes} for widget in widgets.values())
assert sum(node.kind == "ScrollBox" for node in nodes) == 3
for action in ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out"):
    for device in ("keyboard", "controller"):
        assert f"command:{action}:{device}" in widgets
assert widgets["value:third_person:keyboard"].calls["SetText"] == ("P",)
assert widgets["value:zoom_in:keyboard"].calls["SetText"] == ("NONE",)
f.click(form, widgets, "FR")
f.click(form, widgets, "nav:commands")
f.click(form, widgets, "icons:XSX")
duplicate = widgets["command:orbit:keyboard"]
duplicate.SelectedKey = NS(Key=NS(KeyName="P"))
form.poll()
assert settings.commands.option("orbit_key").value == "Seven"
assert form.command_form.notice == "refused"
assert (widgets["commands_status"].calls["SetText"] ==
        ("Attribution refusée. Cette touche est réservée ou déjà utilisée.",))
chosen = widgets["command:zoom_in:controller"]
chosen.SelectedKey = NS(Key=NS(KeyName="Gamepad_LeftShoulder"))
form.poll()
assert settings.commands.option("zoom_in_controller").value == "Gamepad_LeftShoulder"
assert widgets["value:zoom_in:controller"].calls["SetText"] == ("LB",)
assert widgets["command:zoom_in:keyboard"].calls["SetNoKeySpecifiedText"] == ("MODIFIER",)

# An unfinished selector never writes a draft; closing recreates clean controls.
widgets["command:orbit:controller"].selecting = True
assert f.click(form, widgets, "close") and form.close_ready()
root, widgets, reopened = f.build()
assert reopened.page == 1 and widgets["pages"].calls["SetActiveWidgetIndex"] == (1,)
assert reopened.model.language == "FR" and reopened.model.controller_icons == "XSX"
assert not reopened.selecting() and settings.commands.option("orbit_controller").value is None
assert widgets["value:zoom_in:controller"].calls["SetText"] == ("LB",)

# Image brush choice uses the same catalogue as Grapple; the text fallback stays usable.
brush = NS(ResourceObject=object())
table = NS(InputBrushDataMap=[NS(Key=NS(KeyName="Gamepad_LeftShoulder"), KeyBrush=brush)])
reopened.command_catalogue.tables["XSX"] = lambda: table
reopened.refresh_labels(widgets)
assert widgets["value:zoom_in:controller:icon"].calls["SetBrush"] == (brush,)
assert widgets["value:zoom_in:controller"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
f.click(reopened, widgets, "icons:PS5")
assert widgets["value:zoom_in:controller"].calls["SetText"] == ("L1",)

# A close immediately after moving a slider must flush the delayed save.
f.click(reopened, widgets, "nav:camera")
widgets["setting:fov"].value = 132
assert f.click(reopened, widgets, "close")
_, widgets, reopened = f.build()
assert widgets["setting:fov"].value == 132
f.state["refuse_save"] = True
widgets["setting:fov"].value = 140
assert not f.click(reopened, widgets, "close")
assert settings.fov.value == 132 and reopened.notice == "failed"
f.state["refuse_save"] = False
assert f.click(reopened, widgets, "close")

# Disabling gameplay must not make its settings window unusable.
_, widgets, reopened = f.build()
f.click(reopened, widgets, "enabled")
assert not f.mod.is_enabled and reopened.keep_when_disabled
assert f.click(reopened, widgets, "close")

runtime = shared.shared(weak_ref=weakref.ref, address_of=id)
runtime.register("third_person_fov", 150, object(), constants.PROTOCOL)
_, widgets, owned = f.build()
owned.pending["fov"] = 120
owned.shown["fov"] = 120
owned.changed_at = 10**30
runtime.register("apex_movement", 200, object(), constants.PROTOCOL)
owned.poll()
assert "fov" not in owned.pending and owned.notice == "camera_draft_discarded"
assert widgets["notice"].calls["SetText"] == (
    "Mod caméra changé : les réglages caméra non enregistrés ont été annulés.",)
shared.reset_for_tests()

runtime = shared.shared(weak_ref=weakref.ref, address_of=id)
runtime.register("apex_movement", 200, object(), constants.PROTOCOL)
_, widgets, elsewhere = f.build()
assert "heading:command_external" in widgets
assert widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert widgets["camera:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
assert widgets["restore"].calls["SetIsEnabled"] == (False,), "Restore must be disabled without owned settings"
assert f.click(elsewhere, widgets, "close")
shared.reset_for_tests()
print("RESULTAT: TOUS LES TESTS PASSENT")
