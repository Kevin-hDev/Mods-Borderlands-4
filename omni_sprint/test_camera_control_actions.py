"""Omni Sprint uses the generated atomic camera command transaction."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs

sdk_stubs.install()

from omni_sprint import settings
from omni_sprint.camera_control_actions import Actions


class Mod:
    def __init__(self): self.saved = 0
    def save_settings(self): self.saved += 1


mod = Mod()
actions = Actions(settings.commands, mod)
assert actions.assign("shoulder", "keyboard", "K")
assert settings.shoulder_key.value == settings.shoulder_bind.key == "K" and mod.saved == 1
assert actions.assign("orbit", "controller", "Gamepad_FaceButton_Top")
assert settings.orbit_controller.value == settings.orbit_controller_bind.key == "Gamepad_FaceButton_Top"
assert not actions.assign("third_person", "keyboard", "K")
assert actions.defaults() and actions.snapshot() == settings.commands.defaults()
print("RESULTAT: OK")
