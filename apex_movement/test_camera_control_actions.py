"""Camera command changes are saved as one transaction and never leave binds out of sync."""

from movement_test_result import Reporter

result = Reporter("camera command transactions validate, save, restore and compensate failures")

import movement_ui_fixture

movement_ui_fixture.install()

from apex_camera_runtime.camera_commands import CameraCommands
from apex_movement.camera_control_actions import Actions


class Mod:
    def __init__(self):
        self.saved = 0
        self.fail = False

    def save_settings(self):
        self.saved += 1
        if self.fail:
            raise OSError("private path")


commands = CameraCommands(third_person=lambda: None, shoulder=lambda: None, orbit=lambda: None,
                          zoom_in=lambda: None, zoom_out=lambda: None,
                              camera_distance=lambda: None)
mod = Mod()
actions = Actions(commands, mod)

assert actions.assign("third_person", "keyboard", "K")
assert commands.option("third_person_key").value == commands.binds[0].key == "K" and mod.saved == 1
assert actions.assign("shoulder", "keyboard", "ThumbMouseButton")
assert actions.assign("orbit", "controller", "Gamepad_FaceButton_Top")
assert actions.assign("orbit", "controller", None)
saved_before_refusals = mod.saved
assert not actions.assign("orbit", "keyboard", "Escape")
assert not actions.assign("orbit", "controller", "Gamepad_LeftX")
assert not actions.assign("orbit", "keyboard", "K")  # Duplicate camera keys are refused.
assert mod.saved == saved_before_refusals
assert actions.assign("orbit", "keyboard", "CapsLock")  # The slow-walk key may intentionally be shared.

before = actions.snapshot()
mod.fail = True
assert not actions.assign("orbit", "keyboard", "Seven")
assert actions.snapshot() == before and commands.binds[4].key == "CapsLock"
mod.fail = False
assert actions.defaults()
assert actions.snapshot() == commands.defaults()
assert actions.apply(before)
assert actions.snapshot() == before

# Alignment is checked before persistence: failure leaves old values and performs no disk write.
persisted = []
mod.save_settings = lambda: persisted.append(actions.snapshot())
align = commands.align
commands.align = lambda: (_ for _ in ()).throw(RuntimeError("bind unavailable"))
assert not actions.assign("orbit", "keyboard", "Seven")
assert actions.snapshot() == before and persisted == []
commands.align = align
result.success()
