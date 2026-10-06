"""Player mode toggles blend offsets; safety cleanup never waits for animation."""
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.camera_bridge import CameraBridge
from apex_camera_runtime.collision import CollisionResolver
from camera_test_fixtures import Bridge
from native_climb_test_fixture import NativeClimbFixture


class AnimatedBridge(Bridge):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blends = []

    def suspend_orbit(self, suspended, seconds, permission):
        self.blends.append((suspended, seconds))
        self.active = seconds > 0

    def offset_transition_active(self):
        return self.active


class Tests(NativeClimbFixture, unittest.TestCase):
    def prepare(self):
        self.make()
        self.controller.stop()
        self.bridge = AnimatedBridge()
        self.controller.bridge = self.bridge
        self.duration = 0.2
        self.settings.orbit_transition = lambda: self.duration
        self.frame(10)

    def test_entry_starts_offset_at_center_without_replacing_native_mode(self):
        self.prepare()
        self.assertEqual(self.bridge.blends, [(False, 0.2)])
        self.assertEqual(self.bridge.suspended[-1], True)
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertEqual(self.controller._mode_pushes, 1)

    def test_exit_keeps_layer_until_offset_has_reached_center(self):
        self.prepare()
        self.bridge.active = False
        self.settings.enabled = False
        self.frame(20)
        self.assertEqual(self.manager.mode, 'ThirdPerson')
        self.assertTrue(self.controller._hooks_installed)
        self.assertEqual(self.bridge.blends[-1], (True, 0.2))
        self.bridge.active = False
        self.frame(30)
        self.assertEqual(self.manager.mode, 'Default')
        self.assertFalse(self.controller.cleanup_pending)

    def test_disabled_common_animation_stops_without_waiting(self):
        self.prepare()
        self.duration = 0
        self.settings.enabled = False
        self.frame(20)
        self.assertFalse(self.controller.cleanup_pending)

    def test_entry_blends_even_before_native_mode_name_is_confirmed(self):
        self.prepare()
        self.controller.stop()
        self.bridge.blends.clear()
        self.manager.PushActorCameraMode = lambda *_args: None
        self.frame(20)
        self.assertEqual(self.manager.mode, 'Default')
        self.assertEqual(self.bridge.blends, [(False, 0.2)])

    def test_entry_collision_permission_covers_unconfirmed_native_mode_only_while_active(self):
        self.make()
        self.settings.orbit_transition = lambda: 0.2
        view = NS(suspend=lambda _: None, suspend_offset=lambda *_: None,
                  offset_transition_active=lambda: True)
        collision = CollisionResolver(None, None, lambda x: lambda: x, self.notes.append)
        self.controller.bridge = CameraBridge(view, None, self.notes.append, collision)
        self.manager.mode = 'Default'
        self.controller.mode_offset.enter(self.controller, self.pc, self.settings)
        self.assertTrue(collision._mode_allowed(self.manager, self.actor))
        self.actor.ZoomState.bWantsToZoom = True
        self.assertFalse(collision._mode_allowed(self.manager, self.actor))
        self.actor.ZoomState.bWantsToZoom = False
        view.offset_transition_active = lambda: False
        self.assertFalse(collision._mode_allowed(self.manager, self.actor))
        self.assertIsNone(collision.offset_permission)

    def test_turning_off_animation_during_exit_releases_resources(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.duration = 0
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_reenable_reverses_offset_without_adding_another_layer(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.settings.enabled = True
        self.frame(30)
        self.assertEqual(self.bridge.blends[-1], (False, 0.2))
        self.assertEqual(self.controller._mode_pushes, 1)
        self.assertEqual(self.bridge.stops, 0)

    def test_cleanup_is_immediate_during_exit_animation(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.assertTrue(self.controller.cleanup_pending)
        self.controller.stop()
        self.assertFalse(self.controller.cleanup_pending)
        self.assertEqual(self.manager.mode, 'Default')

    def test_lost_character_cancels_exit_without_waiting(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.pc.OakCharacter = None
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_native_aim_interrupts_exit_without_waiting(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.actor.ZoomState.bWantsToZoom = True
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_climb_started_during_exit_is_not_blocked_by_animation(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.ladder.CurrentClimbable = object()
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_scripted_climb_started_during_exit_is_not_delayed(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.animation.CurrentType = 1
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_vehicle_mode_interrupts_exit_without_waiting(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.manager.mode = 'Vehicle'
        self.frame(30)
        self.assertFalse(self.controller.cleanup_pending)

    def test_bridge_refusal_transfers_immediately_to_cleanup(self):
        self.prepare()
        def refused(*_args):
            raise RuntimeError('refused')
        self.bridge.suspend_orbit = refused
        self.settings.enabled = False
        with self.assertRaises(RuntimeError):
            self.frame(20)
        self.assertFalse(self.controller.cleanup_pending)

    def test_animation_cannot_keep_resources_forever_without_native_frames(self):
        self.prepare()
        self.settings.enabled = False
        self.frame(20)
        self.assertTrue(self.controller.cleanup_pending)
        self.frame(300_000_020)
        self.assertFalse(self.controller.cleanup_pending)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
