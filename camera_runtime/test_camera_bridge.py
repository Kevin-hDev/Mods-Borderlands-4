"""Optional alignment cannot take down framing unless its cleanup is unsafe."""
from types import SimpleNamespace as NS
import unittest
from camera_test_fixtures import Hooks, Manager, Settings
from apex_camera_runtime.third_person import ThirdPersonController
from apex_camera_runtime.constants import THIRD_PERSON_RIGHT as RIGHT

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

    def start(self, manager):
        self.active = True
        return True

    def stop(self):
        if self.refuse_stop:
            raise RuntimeError('stop refused')
        self.active = False

    def suspend(self, value):
        self.suspended = value

    def suspend_offset(self, value, _seconds):
        self.suspended = value

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
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        config = self.interaction.starts[0]
        self.assertEqual((config.controller, config.pawn, config.manager, config.camera_module),
                         (0x10000, 0x20000, 0x30000, 0x40000))
        self.assertIs(self.bridge.library, self.view.library)
        self.bridge.suspend(True)
        self.assertTrue(self.bridge.stats().suspended)
        self.assertTrue(self.bridge.set_right(-RIGHT))
        self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_orbit_permission_expires_before_normal_third_person_aiming(self):
        clock = [0]
        self.bridge.shoulder.clock = lambda: clock[0]
        self.bridge.suspend(True)
        manager = NS(GetActorCameraMode=lambda _: 'ThirdPerson')
        self.bridge.suspend_orbit(False, 0.2, lambda *_: False)
        self.assertTrue(self.bridge.offset_transition_active())
        self.assertFalse(self.bridge.shoulder.allows(manager, self.actor))
        clock[0] = 300_000_000
        self.assertFalse(self.bridge.offset_transition_active())
        self.assertTrue(self.bridge.shoulder.allows(manager, self.actor))
        self.assertIsNone(self.bridge.shoulder.permission)

    def test_the_native_camera_starts_without_a_shoulder_the_game_gets_it(self):
        self.assertTrue(self.bridge.start(self.manager, -RIGHT, self.pc))
        self.assertEqual(self.bridge.shoulder.place(0.0, 0.0)[0], -RIGHT)
        self.assertTrue(self.bridge.set_right(RIGHT))
        self.assertEqual(self.bridge.shoulder.right, RIGHT)
        self.bridge.stop()
        self.assertEqual(self.bridge.shoulder.right, 0.0)

    def test_climbing_glides_the_shoulder_over_its_measured_time_and_shows_in_its_mode(self):
        from apex_camera_runtime.transition_catalog import CLIMB_SECONDS
        clock = [0]
        self.bridge.shoulder.clock = lambda: clock[0]
        self.view.suspend_climb = lambda value: setattr(self.view, 'suspended', value)
        self.bridge.start(self.manager, RIGHT, self.pc)
        self.bridge.suspend_climb(True)
        self.assertTrue(self.view.suspended)
        clock[0] = int(CLIMB_SECONDS * 1e9 / 2)
        self.assertAlmostEqual(self.bridge.shoulder.place(0.0, 0.0)[0], RIGHT / 2)
        self.assertTrue(self.bridge.shoulder.allows(NS(GetActorCameraMode=lambda _: 'ThirdPersonClimbing'), None))
        self.bridge.stop()

    def test_an_invalid_shoulder_never_starts_the_native_camera(self):
        self.assertFalse(self.bridge.start(self.manager, float('nan'), self.pc))
        self.assertFalse(self.view.active or self.bridge.pending)

    def test_failed_alignment_start_keeps_view_and_cleans_partial_alignment(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertTrue(self.view.active)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.messages[0], 'aim alignment refused: RuntimeError (start refused)')
        self.assertEqual(len(self.messages), 2)
        self.assertIn('unavailable', self.messages[1])
        self.assertTrue(self.bridge.set_right(-RIGHT))
        self.bridge.suspend(True)
        self.assertTrue(self.view.suspended)
        self.bridge.stop()
        self.assertFalse(self.view.active or self.bridge.pending)

    def test_failed_rollback_remains_owned_and_retryable(self):
        self.interaction.refuse_start = self.interaction.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, RIGHT, self.pc)
        self.assertTrue(self.bridge.pending)
        self.interaction.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_alignment_cleanup_error_does_not_skip_camera_stop(self):
        self.bridge.start(self.manager, RIGHT, self.pc)
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
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertTrue(self.view.active)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.messages[0], 'aim alignment refused: ValueError (Invalid interaction owner)')
        self.assertEqual(len(self.messages), 2)
        self.bridge.stop()

    def test_missing_alignment_warns_once_across_camera_restarts(self):
        self.bridge.interaction = None
        for _ in range(3):
            self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
            self.assertTrue(self.view.active)
            self.bridge.stop()
        warnings = [message for message in self.messages if 'unavailable' in message]
        self.assertEqual(len(warnings), 1)
        self.assertFalse(self.bridge.pending)

    def test_recovered_alignment_can_start_on_next_enable(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.bridge.stop()
        self.interaction.refuse_start = False
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertTrue(self.interaction.active)
        self.bridge.stop()

    def test_partial_framing_failure_is_cleaned_and_not_treated_as_optional(self):
        def broken_start(_manager):
            self.view.active = True
            raise RuntimeError('framing refused')
        self.view.start = broken_start
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, RIGHT, self.pc)
        self.assertFalse(self.view.active or self.interaction.active or self.bridge.pending)

    def test_failed_framing_cleanup_remains_retryable(self):
        def broken_start(_manager):
            self.view.active = True
            raise RuntimeError('framing refused')
        self.view.start = broken_start
        self.view.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.start(self.manager, RIGHT, self.pc)
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


def beam_sdk():
    who = NS(Class=NS(Name='ObjectProperty'), Offset_Internal=0x120)
    state = NS(Class=NS(Name='StructProperty'), Offset_Internal=0x88, Struct=NS(_find_prop=lambda _name: who))
    beam_class = NS(_find_prop=lambda _name: state, ClassDefaultObject=NS(_get_address=lambda: 0x50000))
    return NS(find_class=lambda _name: beam_class)


class BeamTests(unittest.TestCase):
    """The beams follow the eyes: started after them with the same camera, stopped first, and a refused beam
    never takes the eyes or the camera with it."""

    def setUp(self):
        self.view, self.interaction, self.beam = View(), Interaction(), Interaction()
        self.order, self.messages = [], []
        for name, resource in (('beam', self.beam), ('eyes', self.interaction), ('view', self.view)):
            stop = resource.stop
            resource.stop = lambda stop=stop, name=name: (self.order.append(name), stop())
        self.bridge = CameraBridge(self.view, self.interaction, self.messages.append, beam=self.beam, sdk=beam_sdk())
        self.manager = NS(_get_address=lambda: 0x30000)
        self.pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))

    def test_beams_start_after_the_eyes_with_the_same_camera_and_stop_first(self):
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        config = self.beam.starts[0]
        self.assertEqual((config.camera.pawn, config.camera.manager, config.beam_default, config.instigator_offset),
                         (0x20000, 0x30000, 0x50000, 0x1A8))
        self.assertEqual(self.messages, ['third person aim alignment installed', 'third person beam alignment installed'])
        self.bridge.stop()
        self.assertEqual(self.order, ['beam', 'eyes', 'view'])
        self.assertFalse(self.beam.active or self.interaction.active or self.bridge.pending)
        self.assertEqual(self.messages[-2:], ['third person beam alignment released',
                                              'third person aim alignment released'])

    def test_a_refused_beam_keeps_the_eyes_and_warns_once(self):
        self.beam.refuse_start = True
        for _ in range(2):
            self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
            self.assertTrue(self.view.active and self.interaction.active)
            self.assertFalse(self.beam.active)
            self.bridge.stop()
        self.assertEqual([m for m in self.messages if 'beam' in m],
                         ['beam alignment refused: RuntimeError (start refused)',
                          'WARNING: Beam alignment unavailable. Third-person camera remains active; '
                          'beam weapons may land beside the crosshair.'])
        self.assertFalse(self.bridge.pending)

    def test_an_unreadable_beam_layout_starts_no_beam(self):
        self.bridge.sdk = NS(find_class=lambda _name: NS(_find_prop=lambda _name: None))
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertEqual(self.beam.starts, [])
        self.assertTrue(self.interaction.active)
        self.assertIn('beam alignment refused: AttributeError', self.messages[1])
        self.bridge.stop()

    def test_refused_eyes_never_start_beams(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertFalse(self.beam.active)
        self.assertEqual(self.beam.starts, [])
        self.bridge.stop()

    def test_a_beam_that_cannot_be_stopped_stays_owned_but_the_rest_stops(self):
        self.bridge.start(self.manager, RIGHT, self.pc)
        self.beam.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active)
        self.assertTrue(self.bridge.pending)
        self.beam.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.bridge.pending)


class Thrown(Interaction):
    def __init__(self):
        super().__init__()
        self.stops = 0

    def stop(self):
        self.stops += 1
        super().stop()


class ThrownTests(unittest.TestCase):
    """Throws leave the hand with or without the eyes: started last, stopped first, and a refused start never takes
    the camera with it."""

    def setUp(self):
        self.view, self.interaction, self.beam, self.thrown = View(), Interaction(), Interaction(), Thrown()
        self.order, self.messages = [], []
        for name, resource in (('thrown', self.thrown), ('beam', self.beam), ('eyes', self.interaction),
                               ('view', self.view)):
            stop = resource.stop
            resource.stop = lambda stop=stop, name=name: (self.order.append(name), stop())
        self.bridge = CameraBridge(self.view, self.interaction, self.messages.append, beam=self.beam,
                                   sdk=beam_sdk(), thrown=self.thrown)
        self.manager = NS(_get_address=lambda: 0x30000)
        self.pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))

    def test_throws_start_last_with_the_controller_and_stop_first(self):
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertEqual(self.thrown.starts, [self.pc])
        self.assertEqual(self.messages, ['third person aim alignment installed', 'third person beam alignment installed',
                                         'third person throws from the hand installed'])
        self.order.clear()
        self.bridge.stop()
        self.assertEqual(self.order, ['thrown', 'beam', 'eyes', 'view'])
        self.assertFalse(self.thrown.active or self.bridge.pending)
        self.assertEqual(self.messages[-3], 'third person throws from the hand released')

    def test_throws_need_no_eyes(self):
        self.interaction.refuse_start = True
        self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
        self.assertTrue(self.thrown.active)
        self.bridge.stop()

    def test_a_refused_start_is_cleaned_keeps_the_camera_and_warns_once(self):
        self.thrown.refuse_start = True
        for _ in range(2):
            self.assertTrue(self.bridge.start(self.manager, RIGHT, self.pc))
            self.assertTrue(self.view.active and self.interaction.active and self.beam.active)
            self.assertFalse(self.thrown.active or self.bridge._thrown_pending)
            self.bridge.stop()
        self.assertEqual(self.thrown.stops, 2)
        self.assertEqual([m for m in self.messages if 'throws' in m.lower()],
                         ['throws from the hand refused: RuntimeError',
                          'WARNING: Throws from the hand unavailable. Third-person camera remains active; '
                          'thrown objects may appear beside the hunter.'])
        self.assertFalse(self.bridge.pending)

    def test_a_unit_that_cannot_be_stopped_stays_owned_but_the_rest_stops(self):
        self.bridge.start(self.manager, RIGHT, self.pc)
        self.thrown.refuse_stop = True
        with self.assertRaises(RuntimeError):
            self.bridge.stop()
        self.assertFalse(self.view.active or self.interaction.active or self.beam.active)
        self.assertTrue(self.bridge.pending)
        self.thrown.refuse_stop = False
        self.bridge.stop()
        self.assertFalse(self.bridge.pending)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
