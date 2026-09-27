"""A stale Orbit zoom cannot keep the next player-camera unit waiting forever."""

import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bridge, Hooks, Manager, Settings


class ZoomSettings(Settings):
    def __init__(self):
        super().__init__()
        self.orbit = True
        self.distance = 300

    def orbit_distance(self):
        return self.distance

    def set_orbit_distance(self, value):
        self.distance = value


class RefusingOffset:
    def __init__(self):
        self._x, self.Y, self.Z = 0.0, 0.0, 0.0
        self.refuse_zero = False

    @property
    def X(self):
        return self._x

    @X.setter
    def X(self, value):
        if self.refuse_zero and value == 0.0:
            raise RuntimeError("release refused")
        self._x = value


class CleanupTests(unittest.TestCase):
    def test_stale_cleanup_abandons_an_offset_the_old_manager_refuses(self):
        manager, settings = Manager(), ZoomSettings()
        offset = RefusingOffset()
        manager.CameraModeState = NS(CameraLocationOffset=offset)
        actor = NS(Mesh=NS(GetAnimInstance=lambda: object()), ZoomState=None)
        pc = NS(OakCharacter=actor, PlayerCameraManager=manager,
                ClientSetCameraMode=lambda mode: setattr(manager, "mode", mode))
        controller = ThirdPersonController(Hooks(), Bridge(), "zoom-stale-cleanup")
        controller.sync("test", pc, settings, 1)
        self.assertTrue(controller.zoom.change(settings, 1))
        offset.refuse_zero = True

        controller.stop(stale=True)

        self.assertFalse(controller.cleanup_pending)
        self.assertIsNone(controller.zoom.last_offset)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
