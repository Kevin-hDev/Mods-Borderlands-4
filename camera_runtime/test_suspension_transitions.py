"""Climb interpolation never survives a stronger camera authority."""
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.camera_bridge import CameraBridge
from apex_camera_runtime.shoulder_offset import ShoulderOffset
from native_climb_test_fixture import NativeClimbFixture

class Tests(NativeClimbFixture, unittest.TestCase):
    def test_third_person_aim_cancels_orbit_offset_without_suspending_ads(self):
        self.make()
        calls = []
        view = NS(suspend=lambda value: calls.append(value), suspend_offset=lambda *_: None)
        # An Orbit glide under way, whose permission refuses ThirdPerson.
        shoulder = ShoulderOffset(clock=lambda: 0)
        self.controller.bridge = CameraBridge(view, None, self.notes.append, shoulder=shoulder)
        shoulder.show(61.5)
        self.controller.bridge.suspend_orbit(True, 0.5, lambda *_: False)
        self.controller.ads = NS(wanted=True, prepare=lambda *_args, **_kw: True,
                                 confirm=lambda _: None, pending=False)
        self.actor.ZoomState.bWantsToZoom = True
        self.frame(3)
        self.assertEqual(calls, [False])
        self.assertIsNone(shoulder.permission)
        self.assertTrue(shoulder.allows(self.manager, self.actor))

    def test_orbit_uses_shared_timing_and_aim_cancels_even_while_suspended(self):
        self.make()
        calls = []
        self.settings.orbit_transition = lambda: 0.75
        self.bridge.suspend_orbit = lambda value, seconds, permission: calls.append((value, seconds, permission))
        self.bridge.suspend = lambda value: calls.append(('instant', value))
        self.controller.set_desired_mode('Orbit')
        self.assertEqual(calls[0][:2], (True, 0.75))
        self.assertTrue(calls[0][2](self.manager, self.actor))
        self.actor.ZoomState.bWantsToZoom = True
        self.assertFalse(calls[0][2](self.manager, self.actor))
        self.controller._suspend('aim', True)
        self.assertEqual(calls[-1], ('instant', True))

    def test_orbit_return_waits_for_confirmation_and_uses_same_timing(self):
        self.make()
        calls = []
        self.settings.orbit_transition = lambda: 0.4
        self.bridge.suspend_orbit = lambda value, seconds, permission: calls.append((value, seconds))
        self.controller.set_desired_mode('Orbit')
        self.controller.set_desired_mode('ThirdPerson', release_orbit=False)
        self.assertEqual(calls, [(True, 0.4)])
        self.controller.confirm_desired_mode()
        self.assertEqual(calls, [(True, 0.4), (False, 0.4)])

    def test_vehicle_cancels_a_climb_fade_without_temporarily_unsuspending(self):
        self.make()
        calls = []
        self.bridge.suspend_climb = lambda value: calls.append(('climb', value))
        self.bridge.suspend = lambda value: calls.append(('instant', value))
        self.enter()
        self.assertEqual(calls, [('climb', True)])
        self.manager.mode = 'ThirdPersonVehicle'
        self.frame(3)
        self.assertEqual(calls, [('climb', True), ('instant', True)])

    def test_confirmed_third_person_return_uses_the_climb_fade(self):
        self.make()
        calls = []
        self.bridge.suspend_climb = lambda value: calls.append(value)
        self.enter()
        self.ladder.CurrentClimbable = None
        self.frame(3)
        self.assertEqual(calls, [True])
        self.frame(4)
        self.assertEqual(calls, [True, False])

    def test_saved_shoulder_and_duration_reach_the_actual_action(self):
        self.make()
        durations = []
        self.settings.shoulder_transition = lambda: 0.75
        self.bridge.transition_duration = durations.append
        self.assertTrue(self.controller.set_shoulder(self.settings, True))
        self.assertEqual(durations, [0.75])
        self.assertTrue(self.settings.left)

if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
