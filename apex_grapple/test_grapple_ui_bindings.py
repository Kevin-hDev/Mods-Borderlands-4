"""The window uses the real mod's transactions, validation and device separation."""


import control_fixture as f
from apex_grapple import settings
from apex_grapple.control_bindings import Bindings

bindings = Bindings()
f.mod.is_enabled = True
keyboard, pad = f.config.DEVICES
settings.pull_strength.value = 2.0
assert bindings.save(("ThumbMouseButton2",))[0]
assert keyboard.selection() == ("ThumbMouseButton2",) and pad.selection() is None
assert bindings.save(("Gamepad_LeftShoulder", "Gamepad_RightShoulder"))[0]
assert keyboard.selection() == ("ThumbMouseButton2",)
assert pad.selection() == ("Gamepad_LeftShoulder", "Gamepad_RightShoulder")
count = f.mod.saved
for chosen in ((), ("Escape",), ("Tilde",), ("V", "V"), ("MouseScrollUp", "V"),
               ("V", "Gamepad_RightShoulder"), ("NoSuchKey",), ("V", "G", "J")):
    assert not bindings.save(chosen)[0]
assert f.mod.saved == count
f.mod.fail_save = True
assert not bindings.save(("J",))[0]
assert keyboard.selection() == ("ThumbMouseButton2",)
settings.controller_hold.value, settings.hold_time.value = True, 0.8
assert not bindings.reset()[0] and keyboard.selection() == ("ThumbMouseButton2",)
assert settings.controller_hold.value is True and settings.hold_time.value == 0.8, "A failed reset keeps the hold"
f.mod.fail_save = False
assert bindings.reset()[0]
assert keyboard.selection() is None and pad.selection() is None
# The hold mode is a key setting on the CONTROLS page (Kevin, 2026-10-06): the keys' reset puts it back too.
assert all(option.value == option.default_value for option in settings.HOLD)
assert settings.pull_strength.value == 2.0
assert f.mod.is_enabled
f.mod.is_enabled = False
assert not bindings.ready() and not bindings.save(("J",))[0]
print("OK | window save, validation, rollback, both-device reset with the hold mode, gameplay preserved")
