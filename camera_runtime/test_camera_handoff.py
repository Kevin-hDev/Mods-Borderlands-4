"""A failed old-camera cleanup cannot starve the newly elected client."""

import pathlib
import sys
import weakref

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.constants import PROTOCOL  # noqa: E402
from apex_camera_runtime.fov import FovEngine  # noqa: E402
from apex_camera_runtime.runtime import CameraRuntime  # noqa: E402


class Settings:
    def __init__(self, wanted):
        self.wanted = wanted
        self.saved = (None, None)

    def fov_enabled(self):
        return True

    def fov_value(self):
        return self.wanted

    def saved_fov_pair(self):
        return self.saved

    def remember_fov_pair(self, native, applied):
        self.saved = (native, applied)

    def note(self, _message):
        pass


class Player:
    address = 41
    BaseFOV = 90.0


class FailingThird:
    def __init__(self):
        self.armed = False
        self.syncs = 0
        self.stops = 0

    def sync(self, *_args):
        self.armed = True
        self.syncs += 1

    def stop(self):
        self.stops += 1
        if self.armed:
            raise RuntimeError("persistent native refusal")


player = Player()
third = FailingThird()
runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address), third)
runtime.register("omni_sprint", 100, Settings(140.0), PROTOCOL)
runtime.register("apex_movement", 200, Settings(120.0), PROTOCOL)
runtime.tick(player, 1_000_000_000)

try:
    runtime.unregister("apex_movement")
except RuntimeError:
    pass

first_failed = False
try:
    runtime.tick(player, 1_100_000_000)
except RuntimeError:
    first_failed = True

runtime.tick(player, 1_200_000_000)
passed = (first_failed and runtime._active_client is not None
          and runtime._active_client.owner == "omni_sprint"
          and player.BaseFOV == 140.0 and third.stops == 3)
print("RESULTAT:", "TOUS LES TESTS PASSENT" if passed else "1 ECHEC")
raise SystemExit(0 if passed else 1)
