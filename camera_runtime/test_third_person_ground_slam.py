"""A ground slam landing keeps the selected third-person camera without stacking owned modes.

The game lays its GroundSlamExit mode over ours for about 1.4 s after the landing (measured in game on 2026-10-02).
LayeredManager is a model of that: it assumes the game removes its own layer by name. The trial in game of the same
day agrees: the shoulder view came back one frame after seven landings and stayed, Orbit held through three.
"""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.foot_mode import ORBIT_MODE  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

SLAM_EXIT = "GroundSlamExit"
fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class LayeredManager:
    """Camera modes as named layers: the top one is the mode on screen."""

    def __init__(self):
        self.layers = ["Default"]
        self.pushes = 0
        self.pops = 0

    def PushActorCameraMode(self, _actor, mode, *_args):
        self.layers.append(mode)
        self.pushes += 1

    def PopActorCameraMode(self, _actor, mode, *_args):
        del self.layers[len(self.layers) - 1 - self.layers[::-1].index(mode)]
        self.pops += 1

    def GetActorCameraMode(self, _actor):
        return self.layers[-1]


settings = Settings()
manager, bridge = LayeredManager(), Bridge()
actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
pc = types.SimpleNamespace(_get_address=lambda: 41, OakCharacter=actor, PlayerCameraManager=manager)
controller = ThirdPersonController(Hooks(), bridge, identifier="slam")
controller.sync("third_person_fov", pc, settings, 1)

manager.layers.append(SLAM_EXIT)
controller.sync("third_person_fov", pc, settings, 2)
check("the landing of a ground slam goes back to third person at once",
      manager.GetActorCameraMode(actor) == "ThirdPerson" and controller.foot_mode.pending)
check("the recovery replaces the owned layer instead of adding one",
      manager.layers.count("ThirdPerson") == 1 and controller._mode_pushes == 1
      and manager.pushes == 2 and manager.pops == 1)

controller.sync("third_person_fov", pc, settings, 3)
check("the confirmed recovery leaves nothing pending",
      not controller.foot_mode.pending and not controller._recovery_requested)

manager.layers.remove(SLAM_EXIT)
for now in (4, 5):
    controller.sync("third_person_fov", pc, settings, now)
check("the game ending its own slam mode changes nothing",
      manager.layers == ["Default", "ThirdPerson"] and manager.pushes == 2 and manager.pops == 1)
check("the shoulder shift is never suspended by a ground slam", bridge.suspended == [])

controller.stop()
check("stopping after a ground slam leaves no owned layer behind", manager.layers == ["Default"])


class OrbitPC:
    def __init__(self, orbit_manager):
        self.OakCharacter = actor
        self.PlayerCameraManager = orbit_manager
        self.client_modes = []

    def _get_address(self):
        return 42

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        self.PlayerCameraManager.mode = mode


orbit_settings = Settings()
orbit_settings.orbit = True
orbit_manager = Manager()
orbit_pc = OrbitPC(orbit_manager)
orbit = ThirdPersonController(Hooks(), Bridge(), identifier="slam_orbit")
orbit.sync("third_person_fov", orbit_pc, orbit_settings, 10)

orbit_manager.mode = SLAM_EXIT
orbit.sync("third_person_fov", orbit_pc, orbit_settings, 11)
check("the landing of a ground slam asks Orbit again when Orbit is the selected camera",
      orbit_pc.client_modes == [ORBIT_MODE, ORBIT_MODE] and orbit.foot_mode.pending)
orbit.sync("third_person_fov", orbit_pc, orbit_settings, 12)
check("Orbit after a ground slam holds no ThirdPerson layer and stays the saved choice",
      orbit_manager.mode == ORBIT_MODE and orbit_manager.pushes == 0 and orbit._mode_pushes == 0
      and not orbit.foot_mode.pending and orbit_settings.orbit and orbit_settings.notes == [])
orbit.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
