"""Alternating optional refusals never flood the shared SDK journal."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from apex_camera_runtime.framing_session import FramingSession
from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bridge, Hooks, Manager, Settings


class Tests(unittest.TestCase):
    def test_permanent_refusal_is_reported_once(self):
        logs = []
        session = FramingSession(None, None, None, logs.append)
        with patch('time.perf_counter_ns') as clock:
            for second in range(3600):
                clock.return_value = second * 1_000_000_000
                session._report('unavailable')
        self.assertEqual(len(logs), 1)

    def test_changed_refusal_reports_suppressed_count_after_budget(self):
        logs = []
        session = FramingSession(None, None, None, logs.append)
        with patch('time.perf_counter_ns') as clock:
            clock.return_value = 0
            session._report('unavailable')
            clock.return_value = 1_000_000_000
            session._report('zoom_unavailable')
            session._report('position_unavailable')
            self.assertEqual(len(logs), 1)
            clock.return_value = 30_000_000_000
            session._report('position_unavailable')
        self.assertEqual(len(logs), 2)
        self.assertIn('camera position unavailable', logs[-1])
        self.assertIn('suppressed=2', logs[-1])

    def test_suppressed_count_is_cleared_after_each_published_summary(self):
        lines, now = [], [0]
        session = FramingSession(None, None, None, lines.append, clock=lambda: now[0])
        session._report('unavailable')
        now[0] = 1_000_000_000
        session._report('zoom_unavailable')
        session._report('position_unavailable')
        now[0] = 30_000_000_000
        session._report('position_unavailable')
        self.assertIn('suppressed=2', lines[-1])
        now[0] = 31_000_000_000
        session._report('zoom_unavailable')
        now[0] = 60_000_000_000
        session._report('zoom_unavailable')
        self.assertEqual(len(lines), 3)
        self.assertIn('suppressed=1', lines[-1])

    def test_flapping_reason_remains_bounded_for_one_hour(self):
        logs = []
        session = FramingSession(None, None, None, logs.append)
        with patch('time.perf_counter_ns') as clock:
            for frame in range(216000):
                clock.return_value = frame * 16_666_667
                session._report('unavailable' if frame % 2 == 0 else None)
        self.assertLessEqual(len(logs), 120)
        self.assertGreaterEqual(len(logs), 119)

    def test_stop_and_resume_does_not_rearm_incident_budget(self):
        logs = []
        session = FramingSession(None, None, None, logs.append)
        with patch('time.perf_counter_ns', return_value=0):
            session._report('unavailable')
            session.stop()
            session._report(None)
            session._report('unavailable')
        self.assertEqual(len(logs), 1)

    def test_log_failure_cannot_clear_a_published_context(self):
        def failed_sink(_line):
            raise RuntimeError('synthetic sink failure')
        session = FramingSession(None, None, None, failed_sink)
        session._key = ('identity', (0, 10, 0))
        session._report('unavailable')
        self.assertEqual(session._key, ('identity', (0, 10, 0)))
        self.assertEqual(session.reason, 'unavailable')

    def test_camera_activation_retries_failed_sink_with_same_clock_budget(self):
        lines, calls, now = [], [], [0]
        def sink(line):
            calls.append(line)
            if len(calls) == 1:
                raise RuntimeError('synthetic sink failure')
            lines.append(line)
        session = FramingSession(None, None, None, sink, clock=lambda: now[0])
        session._report('unavailable')
        now[0] = 31_000_000_000
        session._report('unavailable')
        self.assertEqual(len(calls), 1)
        pc = NS(_get_address=lambda: 10, OakCharacter=object(), PlayerCameraManager=Manager())
        controller = ThirdPersonController(Hooks(), Bridge(), 'diagnostic-test', framing=session)
        controller._start(pc, Settings(), now[0])
        session._report('unavailable')
        self.assertEqual(len(lines), 1)
        self.assertIn('Camera framing unavailable', lines[0])

    def test_repeated_activation_cannot_reset_the_thirty_second_budget(self):
        lines, now = [], [0]
        session = FramingSession(None, None, None, lines.append, clock=lambda: now[0])
        session._report('unavailable')
        now[0] = 1_000_000_000
        pc = NS(_get_address=lambda: 10, OakCharacter=object(), PlayerCameraManager=Manager())
        controller = ThirdPersonController(Hooks(), Bridge(), 'diagnostic-test', framing=session)
        for _ in range(100):
            controller._start(pc, Settings(), now[0])
            session._report(None)
            session._report('zoom_unavailable')
        self.assertEqual(len(lines), 1)
        now[0] = 30_000_000_000
        session._report('zoom_unavailable')
        self.assertEqual(len(lines), 2)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
