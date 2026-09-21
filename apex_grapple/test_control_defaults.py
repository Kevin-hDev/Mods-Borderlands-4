"""Reset takes every default from its option and preserves unrelated mod state."""

import control_fixture as f
from apex_grapple import control_actions, frame, settings

for option in settings.ALL:
    option.value = not option.default_value if type(option.default_value) is bool else option.max_value
device = f.config.DEVICES[0]
device.mode.value = f.config.DOUBLE
device.first.value, device.second.value = "LeftControl", "ThumbMouseButton2"
before_enabled = f.mod.is_enabled
control_actions.restore(f.control_menu.RESTORE)
assert all(option.value == option.default_value for option in (*settings.ALL, *f.config.ALL))
assert not frame.rope.busy
assert f.mod.saved == 1 and f.mod.is_enabled == before_enabled
assert f.config.groups(f.state["mappings"]) == (("V",), ("Gamepad_RightThumbstick",))

for first, second in [("V", "V"), ("MouseScrollUp", "V"), ("Gamepad_LeftShoulder", "V"), ("Invalid", "V")]:
    device.mode.value = f.config.DOUBLE
    device.first.value, device.second.value = first, second
    assert f.config.groups(f.state["mappings"])[0] == ("V",)

device.mode.value = f.config.SINGLE
device.first.value = "ThumbMouseButton2"
settings.pull_strength.value = 2.0
f.mod.fail_save = True
control_actions.restore(f.control_menu.RESTORE)
assert device.first.value == "ThumbMouseButton2" and settings.pull_strength.value == 2.0
f.mod.fail_save = False
control_actions.save_values(f.mod, tuple((option, option.default_value) for option in device.options))
assert device.mode.value == f.config.GAME and settings.pull_strength.value == 2.0
print("OK | complete reset, save, fallback, device-only reset and failed-save rollback")
