"""Apex Movement applies and gives back its custom FOV through the shared runtime."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import camera, camera_settings  # noqa: E402

character = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, character)
player = state["pc"].Player
camera.start()
camera_settings.custom_fov.value = True
camera_settings.fov.value = 140
camera.on_frame(1_000_000_000)
ok = player.BaseFOV == 140.0
ok = ok and camera_settings.saved_fov_pair() == (90.0, 140.0) and state["settings_saves"] == 1
camera.stop()
ok = ok and player.BaseFOV == 90.0
camera.start()
camera_settings.custom_fov.value = True
camera.on_frame(2_000_000_000)
player.BaseFOV = 105.0
camera.stop()
ok = ok and player.BaseFOV == 105.0

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
