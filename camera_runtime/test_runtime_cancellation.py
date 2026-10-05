"""An invalid window context revokes Orbit without reading or writing its old world."""
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.foot_mode import FootModeState, ORBIT_MODE
from apex_camera_runtime.runtime import CameraRuntime


class Tests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.state = FootModeState()
        self.state.begin(ORBIT_MODE, 1, True, False)
        self.controller = NS(foot_mode=self.state, clock=lambda: 2,
                             cancel_orbit=lambda *_: self.calls.append("physical") or True)
        self.runtime = CameraRuntime(None, self.controller)
        self.runtime.register("camera", 100, NS(note=lambda _: None))

    def test_replaced_controller_context_has_no_physical_restore_or_late_save(self):
        self.assertTrue(self.runtime.cancel_orbit("camera", restore=False))
        self.assertEqual(self.calls, [])
        self.assertIsNone(self.state.transaction)
        self.assertTrue(self.state.rollback_failed)
        writes = []
        self.assertFalse(self.state.settle(self.controller, NS(set_orbit=writes.append), ORBIT_MODE, 3))
        self.assertEqual(writes, [])

    def test_normal_cancellation_retains_the_tracked_physical_restore(self):
        self.assertTrue(self.runtime.cancel_orbit("camera"))
        self.assertEqual(self.calls, ["physical"])

    def test_previous_owner_can_only_revoke_its_own_existing_request_during_handoff(self):
        self.runtime._active_client = self.runtime.arbiter.active()
        self.runtime.register("new_camera", 200, NS(note=lambda _: None))
        self.assertFalse(self.runtime.cancel_orbit("new_camera", restore=False))
        self.assertIsNotNone(self.state.transaction)
        self.assertTrue(self.runtime.cancel_orbit("camera", restore=False))
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
