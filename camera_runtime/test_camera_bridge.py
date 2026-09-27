"""Optional alignment cannot take down framing unless its cleanup is unsafe."""
from types import SimpleNamespace as NS
import unittest
from camera_test_fixtures import Hooks, Manager, Settings
from apex_camera_runtime.third_person import ThirdPersonController

try:
    from apex_camera_runtime.camera_bridge import CameraBridge
except ImportError:
    CameraBridge = None


class View:
    def __init__(self):
        self.library = NS(_handle=0x40000)
        self.active = False
        self.refuse_stop = False
        self.suspended = False

    def start(self, manager, right):
        self.active = True
        return True

    def stop(self):
        if self.refuse_stop:
            raise RuntimeError('stop refused')
        self.active = False

    def suspend(self, value):
        self.suspended = value

    def set_right(self, value):
        return abs(value) == 48.4

    def stats(self):
        return NS(active=int(self.active), suspended=int(self.suspended))


class Interaction:
    def __init__(self):
        self.active = False
        self.refuse_start = self.refuse_stop = False
        self.starts = []

    def start(self, config):
        self.active = True
        if self.refuse_start:
            raise RuntimeError('start refused')
        self.starts.append(config)

    def stop(self):
        self.active = False
        if self.refuse_stop:
            raise RuntimeError('stop refused')


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(CameraBridge, 'Integrated camera bridge is missing')
        self.view, self.interaction = View(), Interaction()
        self.messages = []
        self.bridge = CameraBridge(self.view, self.interaction, self.messages.append)
        self.manager = NS(_get_address=lambda: 0x30000)
        self.actor = NS(_get_address=lambda: 0x20000)
        self.pc = NS(_get_address=lambda: 0x10000, OakCharacter=self.actor)

    def test_one_start_binds_current_player_and_camera(self):
        self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
        config = self.interaction.starts[0]
        self.assertEqual((config.controller, config.pawn, config.manager, config.camera_module),
                         (0x10000, 0x20000, 0x30000, 0x40000))
        self.assertIs(self.bridge.library, self.view.library)
        self.bridge.suspend(True)
        self.assertTrue(self.bridge.stats().suspended)
        self.assertTrue(self.bridge.set_right(-48.4))
        self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_failed_alignment_start_keeps_view_and_cleans_partial_alignment(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
        self.assertTrue(self.view.active)
        self.assertFalse(self.interaction.active)
        self.assertEqual(len(self.messages), 1)
        self.assertIn('unavailable', self.messages[0])
        self.assertTrue(self.bridge.set_right(-48.4))
        self.bridge.suspend(True)
        self.assertTrue(self.view.suspended)
        self.bridge.stop()
        self.assertFalse(self.view.active or self.bridge.pending)

    def test_failed_rollback_remains_owned_and_retryable(self):
        self.interaction.refuse_start = self.interaction.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, 48.4, self.pc)
        self.assertTrue(self.bridge.pending)
        self.interaction.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_alignment_cleanup_error_does_not_skip_camera_stop(self):
        self.bridge.start(self.manager, 48.4, self.pc)
        self.interaction.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.stop()
        self.assertFalse(self.view.active)
        self.assertTrue(self.bridge.pending)
        self.interaction.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.bridge.pending)

    def test_invalid_alignment_config_does_not_disable_valid_framing(self):
        self.pc._get_address = lambda: 1
        self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
        self.assertTrue(self.view.active)
        self.assertFalse(self.interaction.active)
        self.assertEqual(len(self.messages), 1)
        self.bridge.stop()

    def test_missing_alignment_warns_once_across_camera_restarts(self):
        self.bridge.interaction = None
        for _ in range(3):
            self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
            self.assertTrue(self.view.active)
            self.bridge.stop()
        warnings = [message for message in self.messages if 'unavailable' in message]
        self.assertEqual(len(warnings), 1)
        self.assertFalse(self.bridge.pending)

    def test_recovered_alignment_can_start_on_next_enable(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
        self.bridge.stop()
        self.interaction.refuse_start = False
        self.assertTrue(self.bridge.start(self.manager, 48.4, self.pc))
        self.assertTrue(self.interaction.active)
        self.bridge.stop()

    def test_partial_framing_failure_is_cleaned_and_not_treated_as_optional(self):
        def broken_start(_manager, _right):
            self.view.active = True
            raise RuntimeError('framing refused')
        self.view.start = broken_start
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, 48.4, self.pc)
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_failed_framing_cleanup_remains_retryable(self):
        def broken_start(_manager, _right):
            self.view.active = True
            raise RuntimeError('framing refused')
        self.view.start = broken_start
        self.view.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, 48.4, self.pc)
        self.assertTrue(self.bridge.pending)
        self.view.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.view.active or self.bridge.pending)

    def test_controller_owns_failed_setup_until_cleanup_finishes(self):
        manager = Manager()
        manager._get_address = lambda: 0x30000
        self.pc.PlayerCameraManager = manager
        controller = ThirdPersonController(Hooks(), self.bridge, 'integration')
        self.interaction.refuse_start = self.interaction.refuse_stop = True
        with self.assertRaises(RuntimeError):
            controller.sync('apex_movement', self.pc, Settings(), 1)
        self.assertTrue(controller.cleanup_pending and self.bridge.pending)
        self.interaction.refuse_stop = False
        controller.stop()
        self.assertFalse(controller.cleanup_pending or self.bridge.pending)

    def test_controller_keeps_mode_and_shoulder_when_alignment_is_unavailable(self):
        manager = Manager()
        manager._get_address = lambda: 0x30000
        self.pc.PlayerCameraManager = manager
        controller = ThirdPersonController(Hooks(), self.bridge, 'fallback')
        settings = Settings()
        self.interaction.refuse_start = True
        controller.sync('apex_movement', self.pc, settings, 1)
        controller.sync('apex_movement', self.pc, settings, 2)
        self.assertEqual(manager.mode, 'ThirdPerson')
        self.assertEqual(manager.pushes, 1)
        self.assertTrue(controller.toggle_shoulder(settings))
        self.assertTrue(settings.left and self.view.active)
        self.assertFalse(self.interaction.active)
        controller.stop()
        self.assertFalse(controller.cleanup_pending or self.bridge.pending)

    def test_character_change_rebinds_alignment_once(self):
        manager = Manager()
        manager._get_address = lambda: 0x30000
        self.pc.PlayerCameraManager = manager
        controller = ThirdPersonController(Hooks(), self.bridge, 'respawn')
        settings = Settings()
        controller.sync('apex_movement', self.pc, settings, 1)
        controller.sync('apex_movement', self.pc, settings, 2)
        self.assertEqual(len(self.interaction.starts), 1)
        self.pc.OakCharacter = NS(_get_address=lambda: 0x50000)
        controller.sync('apex_movement', self.pc, settings, 3)
        self.assertEqual([x.pawn for x in self.interaction.starts], [0x20000, 0x50000])
        controller.stop()
        self.assertFalse(controller.cleanup_pending or self.bridge.pending)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
