"""Orbit borrows the existing ADS presentation without saving a camera change."""
import unittest
from ads_sdk_test_fixtures import Kind
from orbit_aim_test_fixture import OrbitAimFixture


class Tests(OrbitAimFixture, unittest.TestCase):
    def test_borrow_uses_immediate_native_aim_not_the_shared_mode_blend(self):
        self.make()
        self.aim()
        self.assertEqual(self.camera_calls[0],
                         (':CameraTransition', 'ThirdPerson', ('Default', 0.0, True, True)))
        self.assertEqual(len(self.native.contexts), 1)

    def test_third_person_choice_uses_real_ads_then_returns_to_orbit(self):
        self.make()
        self.aim()
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertTrue(self.ads.wanted)
        self.assertEqual(len(self.native.contexts), 1)
        self.assertEqual(self.controller._desired_mode, 'Orbit')
        self.assertEqual(self.controller._mode_pushes, 0)
        self.assertNotIn('orbit', self.controller._suspensions)
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')
        self.assertFalse(self.ads.wanted)
        self.assertIn('orbit', self.controller._suspensions)
        self.assertTrue(self.controller.orbit_available())
        self.assertTrue(self.settings.orbit)
        self.assertFalse(self.settings.enabled)
        self.assertEqual(self.settings.orbit_saves, 0)

    def test_first_person_choice_keeps_native_aim_and_returns_to_orbit(self):
        self.make(enabled=False)
        self.aim()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.native.contexts, [])
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')
        self.assertTrue(self.controller.orbit_available())

    def test_sniper_uses_native_aim_even_with_third_person_choice(self):
        self.make()
        self.animation.WeaponType = Kind.Sniper
        self.aim()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.native.contexts, [])
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')

    def test_held_third_person_aim_does_not_repeat_camera_requests(self):
        self.make()
        self.aim()
        self.requests.clear()
        for _ in range(10):
            self.frame()
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertEqual(self.requests, [])
        self.assertEqual(len(self.native.contexts), 1)

    def test_zoom_tail_keeps_aim_view_until_native_release_finishes(self):
        self.make()
        self.aim()
        self.native.status.fov_writes, self.native.status.zoom_scale = 1, 0.5
        self.actor.ZoomState.bWantsToZoom = False
        self.frame()
        self.native.status.fov_writes += 1
        self.native.status.zoom_scale = 0.8
        self.frame()
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertTrue(self.settings.orbit)
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')

    def test_native_climb_interrupts_aim_without_changing_orbit_choice(self):
        self.make()
        self.aim()
        self.ladder.CurrentClimbable = object()
        self.manager.mode = 'ladder'
        self.frame()
        self.assertEqual(self.manager.mode, 'ThirdPersonClimbing')
        self.assertFalse(self.ads.wanted)
        self.assertTrue(self.settings.orbit)
        self.actor.ZoomState.bWantsToZoom = False
        self.ladder.CurrentClimbable = None
        self.frame()
        self.frame()
        self.assertEqual(self.manager.mode, 'Orbit')
        self.assertTrue(self.controller.orbit_available())

    def test_reaim_during_return_waits_then_reuses_third_person_choice(self):
        self.make()
        self.aim()
        self.accept = False
        self.release()
        self.assertEqual(self.controller.orbit_aim.phase, 'return')
        self.accept = True
        self.actor.ZoomState.bWantsToZoom = True
        self.requests.clear()
        self.pc.CameraTransition('Default')
        self.assertNotIn('Default', self.requests)
        self.manager.mode = 'Orbit'
        self.frame()
        self.frame()
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertTrue(self.ads.wanted)
        self.assertTrue(self.settings.orbit)
        self.assertIsNone(self.controller._orbit_blocked_identity)
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')

    def test_switching_to_sniper_while_aiming_yields_directly_to_native_view(self):
        self.make()
        self.aim()
        self.requests.clear()
        self.animation.WeaponType = Kind.Sniper
        self.frame()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertNotIn('Orbit', self.requests)
        self.assertFalse(self.ads.wanted)
        self.release()
        self.assertEqual(self.manager.mode, 'Orbit')

    def test_refused_third_person_entry_falls_back_once_until_release(self):
        for throwing in (False, True):
            self.make()
            self.refused_modes = () if throwing else ('ThirdPerson',)
            self.raise_modes = ('ThirdPerson',) if throwing else ()
            self.aim()
            self.now += 900_000_000
            self.frame()
            self.assertEqual(self.manager.mode, 'Default')
            attempts = self.requests.count('ThirdPerson')
            for _ in range(10):
                self.frame()
            self.assertEqual(self.requests.count('ThirdPerson'), attempts)
            self.assertEqual(len(self.logs), 1)
            self.refused_modes = self.raise_modes = ()
            self.release()
            self.aim()
            self.assertEqual(self.manager.mode, 'ThirdPerson')

    def test_refused_orbit_return_keeps_a_safe_base_and_allows_disabling_choice(self):
        self.make()
        self.aim()
        self.refused_modes = ('Orbit',)
        self.release()
        self.now += 900_000_000
        self.frame()
        self.frame()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertTrue(self.settings.orbit)
        self.assertTrue(self.controller.orbit_available())
        self.assertTrue(self.controller.set_orbit(self.settings, False, self.now))
        self.frame()
        self.assertFalse(self.settings.orbit)

    def test_observed_vehicle_takes_priority_without_replacing_its_view(self):
        self.make()
        self.aim()
        self.requests.clear()
        self.manager.mode = 'ThirdPersonVehicle'
        self.frame()
        self.assertEqual(self.manager.mode, 'ThirdPersonVehicle')
        self.assertEqual(self.requests, [])
        self.assertFalse(self.ads.wanted)
        self.assertTrue(self.settings.orbit)

    def test_disabling_camera_during_borrow_revokes_both_owned_presentations(self):
        self.make()
        self.aim()
        self.settings.orbit = False
        self.frame()
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.controller.orbit_aim.busy)
        self.assertFalse(self.ads.wanted)
        self.assertFalse(self.controller.cleanup_pending)

    def test_borrow_preserves_each_base_and_delayed_entry_owns_its_request(self):
        for third in (False, True):
            with self.subTest(third=third):
                self.make(third=third)
                self.accept = False
                self.aim()
                self.assertEqual(self.controller.orbit_aim.phase, 'enter')
                self.assertIn('orbit', self.controller._suspensions)
                self.requests.clear()
                for _ in range(5):
                    self.pc.CameraTransition('Default')
                    self.frame()
                self.assertEqual(self.requests, [])
                self.manager.mode = 'ThirdPerson'
                self.accept = True
                self.frame()
                self.assertTrue(self.ads.wanted)
                self.release()
                self.assertEqual(self.manager.mode, 'Orbit')
                self.assertEqual(self.settings.enabled, third)
                self.assertEqual(self.controller._mode_pushes, 0)

    def test_native_requests_do_not_restart_a_confirmed_borrow(self):
        self.make()
        self.aim()
        self.requests.clear()
        for _ in range(5):
            self.pc.ClientSetCameraMode('Default')
            self.pc.CameraTransition('Default')
            self.frame()
        self.assertEqual(self.requests, [])
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertEqual(len(self.native.contexts), 1)

    def test_vehicle_hook_revokes_borrow_before_native_vehicle_request(self):
        self.make()
        self.aim()
        self.requests.clear()
        self.pc.CameraTransition('ThirdPersonVehicle')
        self.frame()
        self.assertEqual(self.requests, ['ThirdPersonVehicle'])
        self.assertFalse(self.controller.orbit_aim.busy)
        self.assertFalse(self.ads.wanted)
        self.assertTrue(self.settings.orbit)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
