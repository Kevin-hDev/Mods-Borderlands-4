"""Unexpected coordination failures refuse presentation and retain a safe cause."""
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime import ads_coordination
from apex_camera_runtime.ads_feedback import Feedback


class CoordinationTests(unittest.TestCase):
    def controller(self):
        logs, stopped = [], []
        def broken(*_args, **_kwargs):
            raise OSError("C:/private/secret.dll")
        ads = NS(prepare=broken, confirm=broken,
                 stop=lambda: stopped.append(True), feedback=Feedback(logs.append))
        controller = NS(ads=ads, _desired_mode="ThirdPerson", _in_vehicle=False,
                        foot_mode=NS(pending=False), cleanup_retry=NS(pending=False))
        return controller, logs, stopped

    def test_unexpected_prepare_failure_is_not_mislabelled_as_an_unsupported_version(self):
        controller, logs, stopped = self.controller()
        for _ in range(3):
            self.assertFalse(ads_coordination.choose(controller, None, None, None, None))
        self.assertEqual(controller.ads.feedback.reason, "preparation_failed")
        self.assertEqual(len(stopped), 3)
        self.assertEqual(sum("OSError" in line for line in logs), 1)
        self.assertFalse(any("private" in line or "secret" in line for line in logs))

    def test_confirmation_exception_is_diagnosed_once_without_private_details(self):
        controller, logs, stopped = self.controller()
        manager = NS(GetActorCameraMode=lambda _actor: "ThirdPerson")
        for _ in range(3):
            ads_coordination.confirm(controller, None, manager)
        self.assertEqual(controller.ads.feedback.reason, "publication_refused")
        self.assertEqual(len(stopped), 3)
        self.assertEqual(sum("OSError" in line for line in logs), 1)
        self.assertFalse(any("private" in line or "secret" in line for line in logs))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
