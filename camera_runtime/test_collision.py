"""The real native callback resolves fresh geometry and owns its lifetime."""
import ctypes
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from apex_camera_runtime import collision
from apex_camera_runtime.generated_ads import CollisionQuery
from apex_camera_runtime.camera_bridge import CameraBridge


class Function:
    def __init__(self):
        self.callback = None
    def __call__(self, callback):
        self.callback = callback
        return 0


class SDK:
    @staticmethod
    def make_struct(_name, **values):
        return NS(**values)


class Physics:
    def __init__(self):
        self.hit, self.fail, self.calls = False, False, 0
    def SphereTraceSingle(self, *args):
        self.calls += 1
        if self.fail:
            raise ValueError('private cause')
        return self.hit, NS(Distance=20.0, bStartPenetrating=False)
    def LineTraceSingle(self, *args):
        return False, NS()


class CollisionTests(unittest.TestCase):
    def setUp(self):
        self.messages, self.physics = [], Physics()
        self.manager = NS(_get_address=lambda: 0x30000, GetActorCameraMode=lambda _: 'ThirdPerson')
        self.actor = NS(_get_address=lambda: 0x20000, K2_GetActorLocation=lambda: NS(X=0, Y=0, Z=0),
                        CapsuleComponent=NS(GetScaledCapsuleHalfHeight=lambda: 80))
        self.pc = NS(_get_address=lambda: 0x10000, OakCharacter=self.actor, PlayerCameraManager=self.manager)
        self.library = NS(view_set_collision=Function())
        self.resolver = collision.CollisionResolver(self.physics, SDK, lambda x: lambda: x, self.messages.append)
        self.resolver.start(self.library, self.pc, self.manager)
        self.query = CollisionQuery(manager=0x30000, desired=(100, 0, 0), delta=0.016)

    def invoke(self):
        output = (ctypes.c_double * 3)(-1, -1, -1)
        status = self.library.view_set_collision.callback(ctypes.pointer(self.query), output)
        return status, tuple(output)

    def test_fresh_desired_camera_is_traced_and_wall_retracts_without_a_suspension(self):
        self.assertEqual(self.invoke(), (0, (100, 0, 0)))
        self.physics.hit = True
        self.assertEqual(self.invoke(), (0, (20, 0, 0)))
        self.query.desired[:] = (0, 100, 0)
        self.assertEqual(self.invoke(), (0, (0, 20, 0)))
        self.assertEqual(self.physics.calls, 6)

    def test_failures_keep_native_position_and_emit_only_a_bounded_generic_cause(self):
        self.physics.fail = True
        for _ in range(50):
            self.assertEqual(self.invoke(), (1, (-1, -1, -1)))
        self.assertEqual(len(self.messages), 1)
        self.assertIn('ValueError', self.messages[0])
        self.assertNotIn('private cause', self.messages[0])

    def test_identity_loss_does_not_trace_old_character_or_manager(self):
        self.pc.OakCharacter = NS(_get_address=lambda: 0x40000)
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(self.physics.calls, 0)

    def test_expired_weak_identity_is_refused_even_when_its_address_is_reused(self):
        self.resolver.lifetime.actor_ref = lambda: None
        self.pc.OakCharacter = NS(_get_address=lambda: 0x20000,
                                  K2_GetActorLocation=self.actor.K2_GetActorLocation)
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(self.physics.calls, 0)

    def test_broken_log_sink_cannot_escape_the_callback_or_accept_a_failed_trace(self):
        def refuse(_message):
            raise RuntimeError('private log failure')
        self.resolver.note = refuse
        self.physics.fail = True
        for _ in range(3):
            self.assertEqual(self.invoke()[0], 1)

    def test_failed_diagnostic_sink_does_not_disable_later_valid_geometry(self):
        self.resolver.note = lambda _: (_ for _ in ()).throw(RuntimeError('private'))
        self.assertEqual(self.invoke()[0], 0)
        self.resolver.note = self.messages.append
        self.query.desired[:] = (0, 100, 0)
        self.assertEqual(self.invoke(), (0, (0, 100, 0)))

    def test_reference_is_ineligible_during_obstruction_and_smooth_recovery(self):
        self.assertFalse(self.resolver.reference_clear)
        self.invoke()
        self.assertTrue(self.resolver.reference_clear)
        self.physics.hit = True
        self.invoke()
        self.assertFalse(self.resolver.reference_clear)
        self.physics.hit = False
        self.invoke()
        self.assertFalse(self.resolver.reference_clear)

    def test_orbit_and_foreign_thread_never_call_physics(self):
        self.manager.GetActorCameraMode = lambda _: 'Orbit'
        self.assertEqual(self.invoke()[0], 1)
        self.manager.GetActorCameraMode = lambda _: 'ThirdPerson'
        self.resolver.thread = -1
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(self.physics.calls, 0)
        self.assertEqual(self.resolver.diagnostics.errors, 0)

    def test_callback_is_pinned_until_native_stop_is_confirmed(self):
        view = NS(library=self.library, start=lambda *_: True, stop=lambda: None)
        bridge = CameraBridge(view, None, self.messages.append, collision=self.resolver)
        self.resolver.release()
        bridge.start(self.manager, 35, self.pc)
        callback = self.resolver.callback
        def refuse():
            raise RuntimeError('stop refused')
        view.stop = refuse
        with self.assertRaises(RuntimeError):
            bridge.stop()
        self.assertIs(self.resolver.callback, callback)
        view.stop = lambda: None
        bridge.stop()
        self.assertIsNone(self.resolver.callback)

    def test_reentrant_release_keeps_the_executing_thunk_until_next_start(self):
        previous = self.resolver.callback
        self.resolver.busy = True
        self.resolver.release()
        self.assertIs(self.resolver.callback, previous)
        self.resolver.busy = False
        self.resolver.start(self.library, self.pc, self.manager)
        self.assertIsNot(self.resolver.callback, previous)

    def test_low_cover_does_not_trace_from_the_characters_waist(self):
        # The game's current camera is above low cover. Only our lateral step is new.
        self.query.before[:] = (-257, 0, 80)
        self.query.desired[:] = (-257, 40, 80)
        traces = []
        def low_cover(*args):
            traces.append((args[1], args[2]))
            return args[1].Z < 50, NS(Distance=22, bStartPenetrating=False)
        self.physics.SphereTraceSingle = low_cover
        self.assertEqual(self.invoke(), (0, (-257, 40, 80)))
        self.assertTrue(all(first.Z == 80 and last.Z == 80 for first, last in traces))

    def test_native_position_needing_no_custom_step_never_calls_physics(self):
        self.query.before[:] = self.query.desired[:]
        self.assertEqual(self.invoke(), (0, (100, 0, 0)))
        self.assertEqual(self.physics.calls, 0)

    def test_late_collision_failure_is_logged_after_a_long_session(self):
        # A periodic report must not exhaust the separate error diagnostics.
        with patch.object(collision.time, 'perf_counter_ns', return_value=0):
            for _ in range(16000):
                self.assertEqual(self.invoke()[0], 0)
        self.physics.fail = True
        self.assertEqual(self.invoke()[0], 1)
        self.assertTrue(any('ValueError' in line for line in self.messages))

    def test_restart_resets_diagnostic_counts_and_reports_again(self):
        self.invoke()
        self.resolver.release()
        self.resolver.start(self.library, self.pc, self.manager)
        before = len(self.messages)
        self.invoke()
        self.assertGreater(len(self.messages), before)

    def test_pillar_hiding_upper_body_slides_toward_native_center_not_toward_pawn(self):
        self.query.before[:] = (-250, 0, 80)
        self.query.desired[:] = (-250, 40, 80)
        self.physics.LineTraceSingle = lambda *args: (args[1].Y > 20, NS())
        self.assertEqual(self.invoke(), (0, (-250, 20, 80)))
        for _ in range(120):
            status, position = self.invoke()
        self.assertEqual(status, 0)
        self.assertEqual(position[0], -250)
        self.assertEqual(position[2], 80)
        self.assertLessEqual(position[1], 20.001)
        self.assertGreater(position[1], 15)
        self.assertFalse(self.resolver.reference_clear)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
