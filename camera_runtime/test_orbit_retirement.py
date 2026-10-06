"""Late Orbit replies cannot steal a native priority or outlive their context."""
import unittest
from types import SimpleNamespace as NS
from orbit_first_person_test_fixture import OrbitFirstPersonFixture
from apex_camera_runtime.cleanup_retry import CLEANUP_RETRY_FIRST_NS, MAX_CLEANUP_ATTEMPTS


class Tests(OrbitFirstPersonFixture, unittest.TestCase):
    def pending_entry(self):
        self.prepare()
        self.accept = False
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()

    def test_late_reply_during_aiming_returns_to_native_first_person(self):
        self.pending_entry()
        self.actor.ZoomState.bWantsToZoom = True
        self.tick()
        self.accept = True
        self.manager.mode = 'Orbit'
        self.tick()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.controller.cleanup_pending)

    def test_late_reply_during_vehicle_keeps_the_native_vehicle_view(self):
        self.pending_entry()
        self.manager.mode = 'ThirdPersonVehicle'
        self.tick()
        self.accept = True
        self.manager.mode = 'Orbit'
        self.tick()
        self.assertEqual(self.manager.mode, 'ThirdPersonVehicle')

    def test_late_reply_after_owner_transfer_uses_current_context_without_old_saves(self):
        self.pending_entry()
        self.runtime.register('new_camera', 200, self.settings)
        self.accept = True
        self.runtime.tick(self.pc, self.now + 10)
        self.manager.mode = 'Orbit'
        self.runtime.tick(self.pc, self.now + 20)
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.settings.orbit)

    def test_refused_recovery_retries_then_confirms_without_reloading(self):
        self.pending_entry()
        self.runtime.cancel_orbit('camera')
        self.accept = True
        self.tick()
        self.manager.mode = 'Orbit'
        self.accept = False
        self.tick()
        self.assertEqual(self.manager.mode, 'Orbit')
        self.accept = True
        self.now += CLEANUP_RETRY_FIRST_NS
        self.tick()
        self.tick()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertTrue(self.runtime.camera_ready('camera'))
        self.assertEqual(self.setups, 1)

    def test_refused_recovery_is_bounded_and_reports_one_generic_warning(self):
        self.pending_entry()
        self.runtime.cancel_orbit('camera')
        self.accept = True
        self.tick()
        self.manager.mode = 'Orbit'
        self.accept = False
        before = len(self.requests)
        for _ in range(MAX_CLEANUP_ATTEMPTS + 3):
            self.now += CLEANUP_RETRY_FIRST_NS
            self.tick()
        self.assertEqual(len(self.requests) - before, MAX_CLEANUP_ATTEMPTS)
        self.assertEqual(len(self.settings.notes), 1)

    def test_changed_context_cannot_receive_the_old_recovery(self):
        self.pending_entry()
        self.runtime.cancel_orbit('camera')
        self.accept = True
        self.tick()
        self.pc.OakCharacter = NS()
        self.manager.mode = 'Orbit'
        before = list(self.requests)
        self.tick()
        self.assertEqual(self.requests, before)
        self.assertIsNone(self.runtime.orbit_entry.retirement.identity)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
