"""Custom settings keep the saved options authoritative, including failure rollback; a choice is one of its names."""

import math
import control_fixture as f
from apex_grapple import look_settings, menu, panel_model as p, settings

model = p.Model(f.mod)
assert p.language.default_value == "EN" and model.language == "EN"
before = tuple(option.value for option in settings.ALL)
assert len(model.options) == 32 and model.groups == (menu.shot, menu.pull, menu.release, menu.look)
assert model.change_language("FR") and model.language == "FR"
assert tuple(option.value for option in settings.ALL) == before
assert not model.change_language("unknown") and model.language == "FR"
assert model.change_language("EN")
assert model.write({"pull_strength": 2.34})
assert math.isclose(settings.pull_strength.value, 2.3)
assert model.write({"grapple_range": 502}) and settings.grapple_range.value == 500
snapshot = tuple(option.value for option in settings.ALL)
for values in ({"unknown": 1}, {"show_rope": 1}, {"hook_speed": float("nan")},
               {"hook_speed": float("inf")}, {"hook_speed": -2}, {"hook_speed": True},
               # A choice takes one of its own names only: not another row's, nor a number, nor None.
               {"look": "Classic"}, {"look": None}, {"rope_light": 2}, {"hook_size": "K"}, {"rope_look": ""}):
    assert not model.write(values)
    assert tuple(option.value for option in settings.ALL) == snapshot
assert not model.write({"punch_range": 900})  # Must stay below the current hook range.
assert model.write({"look": look_settings.CLASSIC, "rope_light": "3"})
assert look_settings.look.value == look_settings.CLASSIC and look_settings.rope_light.value == "3"
snapshot = tuple(option.value for option in settings.ALL)
f.mod.fail_save = True
assert not model.write({"pull_strength": 3.0})
assert tuple(option.value for option in settings.ALL) == snapshot
assert not model.change_language("FR") and model.language == "EN"
f.mod.fail_save = False
assert model.change_language("FR")
assert model.restore() and settings.pull_strength.value == settings.pull_strength.default_value
# RESTORE DEFAULTS and UNDO cover the look's choices too: they walk settings.ALL.
assert all(option.value == option.default_value for option in look_settings.ALL)
assert model.language == "FR" and model.can_undo
assert model.undo() and tuple(option.value for option in settings.ALL) == snapshot
assert not model.can_undo
f.mod.is_enabled = False
assert model.write({"show_rope": False})  # Editing settings does not enable gameplay.
assert not f.mod.is_enabled
assert model.toggle_enabled() and f.mod.is_enabled
assert model.toggle_enabled() and not f.mod.is_enabled
print("OK | custom menu: defaults, locale, bounds, steps, choices, transactions, reset undo, disabled editing")
