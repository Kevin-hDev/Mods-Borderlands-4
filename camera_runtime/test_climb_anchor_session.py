"""Automatic climb ownership exercises the real controller and native boundary."""
import types
import unittest

from apex_camera_runtime.climb_anchor import ClimbAnchorSession
from native_climb_test_fixture import NativeClimbFixture


class Function:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *arguments):
        return self.callback(*arguments)


class AnchorTests(NativeClimbFixture, unittest.TestCase):
    def setup_anchor(self):
        self.make()
        self.native_active = False
        self.start_count = self.stop_count = self.refresh_count = 0
        self.stop_refused = self.start_refused = self.refresh_refused = False
        self.manager._get_address = lambda: 0x30000
        self.actor._get_address = lambda: 0x20000
        self.actor.Mesh = types.SimpleNamespace(_get_address=lambda: 0x40000)
        self.pc.Pawn = self.actor
        self.pc._get_address = lambda: 0x10000
        self.manager.CameraModeState = types.SimpleNamespace(_get_address=lambda: 0x50000)
        self.manager.CameraModeInputs = types.SimpleNamespace(
            _get_address=lambda: 0x60000, Controller=self.pc)
        self.references = (self.manager, self.manager.CameraModeState,
                           self.manager.CameraModeInputs, self.pc, self.actor, self.actor.Mesh)
        for item in self.references:
            item.serial = 0
        self.controller._lifetime.bind(self.pc, self.actor, self.manager)

        def weak(item):
            item.serial = 19
            return lambda: item

        def start(manager):
            self.start_count += 1
            if self.start_refused or manager != 0x30000 or any(item.serial == 0 for item in self.references):
                return 2
            self.native_active = True
            return 0

        def stop():
            self.stop_count += 1
            self.native_active = False
            return int(self.stop_refused)

        def refresh():
            self.refresh_count += 1
            return int(self.refresh_refused)

        library = types.SimpleNamespace(anchor_start=Function(start), anchor_stop=Function(stop),
                                        anchor_refresh=Function(refresh), anchor_stats=Function(lambda _: 0))
        self.controller.anchor = ClimbAnchorSession(library, weak, self.notes.append)

    def test_fresh_first_climb_works_without_aiming_or_probe_command(self):
        self.setup_anchor()
        self.enter()
        self.frame(3)
        self.assertTrue(self.native_active)
        self.assertTrue(self.controller.anchor.pending)
        self.assertEqual(self.start_count, 1)
        self.assertEqual(self.refresh_count, 2)
        self.assertTrue(all(item.serial > 0 for item in self.references))
        self.assertEqual(self.manager.mode, 'ThirdPersonClimbing')

    def test_detached_top_animation_retains_anchor_until_return(self):
        self.setup_anchor()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.animation.CurrentType = 4
        self.frame(3)
        self.assertTrue(self.native_active)
        self.animation.CurrentType = 0
        self.frame(4)
        self.frame(5)
        self.assertFalse(self.native_active)
        self.assertFalse(self.controller.anchor.pending)
        self.assertEqual(self.stop_count, 1)
        self.assertEqual(self.manager.mode, 'ThirdPerson')

    def test_vehicle_and_disable_release_anchor(self):
        for vehicle in (True, False):
            self.setup_anchor()
            self.enter()
            if vehicle:
                self.manager.mode = 'ThirdPersonVehicle'
            else:
                self.settings.enabled = False
            self.frame(3)
            self.assertFalse(self.native_active)
            self.assertFalse(self.controller.anchor.pending)

    def test_rejected_start_is_reported_once_without_per_frame_retries(self):
        self.setup_anchor()
        self.start_refused = True
        self.enter()
        self.frame(3)
        self.frame(4)
        self.assertFalse(self.native_active)
        self.assertEqual(self.start_count, 1)
        self.assertFalse(self.controller.anchor.pending)
        self.assertTrue(any('anchor' in note and 'unavailable' in note for note in self.notes))
        self.assertTrue(any('stage=start code=2' in note for note in self.notes))

    def test_refresh_refusal_disarms_and_does_not_reinstall_each_frame(self):
        self.setup_anchor()
        self.enter()
        self.refresh_refused = True
        self.frame(3)
        self.frame(4)
        self.assertFalse(self.native_active)
        self.assertFalse(self.controller.anchor.pending)
        self.assertEqual(self.start_count, 1)

    def test_failed_stop_stays_owned_until_existing_cleanup_succeeds(self):
        self.setup_anchor()
        self.enter()
        self.stop_refused = True
        with self.assertRaises(RuntimeError):
            self.controller.stop()
        self.assertFalse(self.native_active)
        self.assertTrue(self.controller.anchor.pending)
        self.assertTrue(self.controller.cleanup_pending)
        self.stop_refused = False
        self.controller.stop()
        self.assertFalse(self.controller.cleanup_pending)

    def test_refresh_failure_can_recover_on_the_next_complete_traversal(self):
        self.setup_anchor()
        self.enter()
        self.refresh_refused = True
        self.frame(3)
        self.ladder.CurrentClimbable = None
        self.frame(4)
        self.frame(5)
        self.refresh_refused = False
        self.enter()
        self.assertTrue(self.native_active)
        self.assertEqual(self.start_count, 2)

    def test_owner_change_releases_old_anchor_before_new_camera(self):
        self.setup_anchor()
        self.enter()
        self.pc.OakCharacter = types.SimpleNamespace(
            CharacterMovement=types.SimpleNamespace(
                LadderState=types.SimpleNamespace(CurrentClimbable=None),
                LadderAnimState=types.SimpleNamespace(CurrentType=0)))
        self.frame(3)
        self.assertFalse(self.native_active)
        self.assertFalse(self.controller.anchor.pending)
        self.assertEqual(self.stop_count, 1)

    def test_return_timeout_cannot_rearm_after_controller_shutdown(self):
        self.setup_anchor()
        self.enter()
        self.accept = False
        self.ladder.CurrentClimbable = None
        self.frame(3)
        self.frame(900_000_004)
        self.assertFalse(self.native_active)
        self.assertFalse(self.controller.cleanup_pending)
        self.assertEqual(self.start_count, 1)

    def test_ads_cleanup_wait_does_not_start_an_anchor(self):
        self.setup_anchor()
        self.controller.ads = types.SimpleNamespace(stop=lambda: False, pending=True)
        self.enter()
        self.frame(900_000_004)
        self.assertTrue(self.controller.cleanup_retry.waiting)
        self.assertFalse(self.native_active)
        self.assertEqual(self.start_count, 0)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
