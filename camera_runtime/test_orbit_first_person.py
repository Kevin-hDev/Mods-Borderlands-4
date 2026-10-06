"""Orbit borrows a first-person context without changing the saved base view."""
import unittest
from orbit_first_person_test_fixture import OrbitFirstPersonFixture


class Tests(OrbitFirstPersonFixture, unittest.TestCase):
    def test_first_person_exit_reaches_native_default_without_orbit_rewrite(self):
        self.prepare()
        self.enter_orbit()
        self.requests.clear()
        self.assertTrue(self.runtime.set_orbit('camera', False))
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.requests, ['Default'])
        self.assertTrue(self.settings.orbit)
        self.assertTrue(self.controller.foot_mode.pending)
        self.tick()
        self.tick()
        self.assertFalse(self.settings.orbit)
        self.assertFalse(self.runtime.base_view_locked('camera'))
        self.assertTrue(self.runtime.camera_ready('camera'))
        self.assertFalse(self.controller.cleanup_pending)

    def test_delayed_first_person_exit_waits_for_confirmation_then_unlocks(self):
        self.prepare()
        self.enter_orbit()
        self.accept = False
        self.requests.clear()
        self.assertTrue(self.runtime.set_orbit('camera', False))
        self.assertEqual(self.requests, ['Default'])
        self.tick()
        self.assertTrue(self.settings.orbit)
        self.assertTrue(self.runtime.base_view_locked('camera'))
        self.assertFalse(self.runtime.camera_ready('camera'))
        self.assertIn('orbit', self.controller._suspensions)
        self.accept = True
        self.manager.mode = 'Default'
        self.tick()
        self.tick()
        self.assertFalse(self.settings.orbit)
        self.assertFalse(self.runtime.base_view_locked('camera'))
        self.assertFalse(self.controller.cleanup_pending)

    def test_rejected_first_person_exit_restores_orbit_and_allows_another_exit(self):
        self.prepare()
        self.enter_orbit()
        self.accept = False
        self.assertTrue(self.runtime.set_orbit('camera', False))
        self.now += 900_000_000
        self.tick()
        self.tick()
        self.assertTrue(self.settings.orbit)
        self.assertEqual(self.manager.mode, 'Orbit')
        self.assertTrue(self.runtime.camera_ready('camera'))
        self.accept = True
        self.assertTrue(self.runtime.toggle_orbit('camera'))
        self.tick()
        self.assertFalse(self.settings.orbit)
        self.assertEqual(self.manager.mode, 'Default')

    def test_cold_first_person_loads_only_on_request_and_never_pushes_third_person(self):
        self.prepare()
        self.assertEqual(self.setups, 0)
        self.assertTrue(self.runtime.camera_ready('camera'))
        self.enter_orbit()
        self.assertEqual(self.setups, 1)
        self.assertFalse(self.settings.enabled)
        self.assertEqual(self.manager.pushes, 0)
        self.assertTrue(self.runtime.toggle_orbit('camera'))
        self.tick()
        self.tick()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.settings.orbit)
        self.assertFalse(self.controller.cleanup_pending)

    def test_third_person_returns_to_the_same_shoulder(self):
        self.prepare(third=True)
        self.settings.left = True
        self.tick()
        self.enter_orbit()
        self.assertFalse(self.runtime.toggle_shoulder('camera'))
        self.assertTrue(self.runtime.toggle_orbit('camera'))
        self.tick()
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertEqual(self.controller._mode_pushes, 1)
        self.assertTrue(self.settings.enabled)
        self.assertTrue(self.settings.left)

    def test_zoom_is_available_in_orbit_with_saved_third_person_off(self):
        self.prepare()
        self.enter_orbit()
        self.assertTrue(self.controller.zoom.available())

    def test_cancel_cold_request_does_not_load_or_save_camera(self):
        self.prepare()
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.assertTrue(self.runtime.cancel_orbit('camera'))
        self.tick()
        self.assertEqual(self.setups, 0)
        self.assertFalse(self.settings.orbit)
        self.assertEqual(self.requests, [])

    def test_context_loss_revokes_request_without_touching_previous_pawn(self):
        self.prepare()
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.pc.OakCharacter = None
        self.tick()
        self.assertFalse(self.settings.orbit)
        self.assertEqual(self.requests, [])
        self.assertEqual(self.settings.orbit_rejections, 1)

    def test_first_person_aim_is_not_an_orbit_entry_context(self):
        self.prepare()
        self.actor.ZoomState.bWantsToZoom = True
        self.tick()
        self.assertFalse(self.runtime.camera_ready('camera'))
        self.assertFalse(self.runtime.toggle_orbit('camera'))
        self.assertEqual(self.setups, 0)

    def test_refused_orbit_rolls_back_to_first_person_without_a_layer(self):
        self.prepare()
        self.accept = False
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()
        self.now += 900_000_000
        self.tick()
        self.tick()
        self.assertFalse(self.settings.orbit)
        self.assertFalse(self.settings.enabled)
        self.assertEqual(self.manager.pushes, 0)
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.controller.cleanup_pending)

    def test_save_failure_rolls_back_to_first_person(self):
        self.prepare()
        def refused(_value):
            raise OSError('save refused')
        self.settings.set_orbit = refused
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()
        self.tick()
        self.tick()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.manager.pushes, 0)
        self.assertFalse(self.controller.cleanup_pending)
        self.assertTrue(self.settings.notes)

    def test_other_owner_cannot_queue_a_first_person_request(self):
        self.prepare()
        self.assertFalse(self.runtime.set_orbit('other', True))
        self.assertFalse(self.runtime.camera_ready('other'))
        self.assertEqual(self.setups, 0)

    def test_vehicle_preempts_unconfirmed_entry_without_default_camera_write(self):
        self.prepare()
        self.accept = False
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()
        self.manager.mode = 'ThirdPersonVehicle'
        self.tick()
        self.assertEqual(self.manager.mode, 'ThirdPersonVehicle')
        self.assertEqual(self.requests, ['Orbit'])
        self.assertFalse(self.controller.cleanup_pending)

    def test_climb_preempts_unconfirmed_entry_without_default_camera_write(self):
        self.prepare()
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()
        self.ladder.CurrentClimbable = object()
        self.manager.mode = 'ladder'
        self.tick()
        self.assertNotIn('Default', self.requests)
        self.assertFalse(self.controller.cleanup_pending)

    def test_third_person_shortcut_cannot_change_the_return_view_during_orbit(self):
        self.prepare()
        writes = []
        self.settings.set_third_person = writes.append
        self.enter_orbit()
        self.assertFalse(self.runtime.toggle_third_person('camera'))
        self.assertEqual(writes, [])

    def test_third_person_shortcut_is_locked_during_deferred_entry(self):
        self.prepare()
        writes = []
        self.settings.set_third_person = writes.append
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.assertFalse(self.runtime.toggle_third_person('camera'))
        self.assertEqual(writes, [])

    def test_late_orbit_reply_after_rollback_is_corrected_without_loading_again(self):
        self.prepare()
        self.assertTrue(self.runtime.set_orbit('camera', True))
        self.tick()
        self.assertTrue(self.runtime.cancel_orbit('camera'))
        self.tick()
        self.assertFalse(self.controller.cleanup_pending)
        starts = self.bridge.starts
        self.manager.mode = 'Orbit'
        self.tick()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.bridge.starts, starts)
        self.assertFalse(self.settings.orbit)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
