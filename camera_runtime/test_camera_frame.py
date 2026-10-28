"""The frame coordinator cleans up a failed climb publication and waits for ADS."""
import types
import unittest

from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bridge, Hooks, Manager, Settings


class CameraFrameTests(unittest.TestCase):
    def make(self):
        manager, bridge, settings = Manager(), Bridge(), Settings()
        actor = types.SimpleNamespace(CharacterMovement=types.SimpleNamespace(
            LadderState=types.SimpleNamespace(CurrentClimbable=None),
            LadderAnimState=types.SimpleNamespace(CurrentType=0)))
        requests = []
        def request(mode):
            requests.append(mode)
            manager.mode = mode
        pc = types.SimpleNamespace(_get_address=lambda: 12, OakCharacter=actor,
            PlayerCameraManager=manager, ClientSetCameraMode=request)
        controller = ThirdPersonController(Hooks(), bridge, "frame")
        controller.sync("apex_movement", pc, settings, 1)
        actor.CharacterMovement.LadderState.CurrentClimbable = object()
        manager.mode = "ladder"
        return controller, pc, settings, manager, bridge, requests

    def test_suspension_failure_cannot_leave_partial_climb_ownership(self):
        controller, pc, settings, manager, bridge, _requests = self.make()
        def refused(_value):
            raise RuntimeError("private details")
        bridge.suspend = refused
        with self.assertRaises(RuntimeError):
            controller.sync("apex_movement", pc, settings, 2)
        self.assertFalse(controller.cleanup_pending)
        self.assertEqual(manager.pops, 1)
        self.assertFalse(controller.climb.busy)

    def test_aim_cleanup_timeout_transfers_to_existing_retry_owner(self):
        controller, pc, settings, _manager, _bridge, requests = self.make()
        controller.ads = types.SimpleNamespace(stop=lambda: False, pending=True)
        controller.sync("apex_movement", pc, settings, 2)
        controller.sync("apex_movement", pc, settings, 900_000_003)
        self.assertTrue(controller.cleanup_retry.waiting)
        self.assertNotIn("ThirdPersonClimbing", requests)

    def test_unavailable_attachment_does_not_guess_that_climbing_ended(self):
        controller, pc, settings, manager, _bridge, requests = self.make()
        controller.sync("apex_movement", pc, settings, 2)
        pc.OakCharacter.CharacterMovement = None
        controller.sync("apex_movement", pc, settings, 3)
        self.assertEqual(manager.mode, "ThirdPersonClimbing")
        self.assertEqual(requests, ["ThirdPersonClimbing"])
        self.assertIn("climb", controller._suspensions)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
