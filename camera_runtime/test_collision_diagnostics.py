"""Collision totals stay live while incident output is independently rate-limited."""
import unittest
from apex_camera_runtime.collision_diagnostics import CollisionDiagnostics


class Tests(unittest.TestCase):
    def setUp(self):
        self.lines = []
        self.stats = CollisionDiagnostics(self.lines.append)

    def test_periodic_totals_continue_for_long_sessions_and_include_mean_cost(self):
        for sample in range(40):
            self.stats.record(sample * 30_000_000_000, 2000)
        self.assertEqual(len(self.lines), 40)
        self.assertIn('frames=40 errors=0', self.lines[-1])
        self.assertIn('mean_us=2.0', self.lines[-1])
        self.stats.record(1_200_000_000_000, 4000, error=ValueError('secret'))
        self.assertTrue(any('ValueError' in line for line in self.lines))
        self.assertNotIn('secret', '\n'.join(self.lines))

    def test_the_totals_leave_the_console_and_incidents_keep_it(self):
        """Kevin, 2026-10-10: the 30 s totals read as an endless error in the console."""
        quiet = []
        stats = CollisionDiagnostics(self.lines.append, quiet.append)
        stats.record(0, 1000)
        stats.record(1, 1000, error=ValueError('camera folded onto the hunter'), held=True)
        stats.record(30_000_000_000, 1000)
        self.assertEqual(len(quiet), 2)
        self.assertTrue(all(line.startswith('camera collision frames=') for line in quiet))
        self.assertEqual(len(self.lines), 1)
        self.assertIn('camera folded onto the hunter', self.lines[0])

    def test_the_mods_own_refusals_say_their_reason(self):
        self.stats.record(0, 1000, error=ValueError('Camera collision identity unavailable'))
        self.assertIn('ValueError (Camera collision identity unavailable)', self.lines[0])

    def test_a_held_camera_says_so_instead_of_native(self):
        self.stats.record(0, 1000, error=ValueError('Camera collision identity unavailable'), held=True)
        self.assertIn('previous position held: ValueError (Camera collision identity unavailable)', self.lines[0])
        self.assertNotIn('native', self.lines[0])

    def test_the_known_refusals_are_the_ones_the_collision_files_raise(self):
        import pathlib
        import re
        from apex_camera_runtime import collision_config
        folder = pathlib.Path(collision_config.__file__).parent
        raised = {match for path in (*folder.glob('collision*.py'), folder / 'camera_guard.py')
                  for match in re.findall(r"raise ValueError\(['\"]([^'\"]+)['\"]\)", path.read_text(encoding='utf-8'))}
        self.assertEqual(raised, set(collision_config.KNOWN_REFUSALS))

    def test_continuous_failures_and_frame_flapping_cannot_spam_incidents(self):
        for sample in range(200):
            self.stats.record(sample * 1_000_000, 1000,
                              error=ValueError() if sample % 2 == 0 else None)
        self.assertEqual(sum('ValueError' in line for line in self.lines), 1)
        self.stats.record(2_000_000_000, 1000)
        self.stats.record(2_001_000_000, 1000, error=ValueError())
        self.assertEqual(sum('ValueError' in line for line in self.lines), 1)
        self.assertEqual(self.stats.errors, 101)

    def test_restart_does_not_inherit_totals_or_a_disabled_sink(self):
        def fail(_):
            raise RuntimeError()
        self.stats.note = fail
        self.stats.record(0, 1000)
        self.stats.reset()
        self.stats.note = self.lines.append
        self.stats.record(0, 3000)
        self.assertIn('frames=1 errors=0', self.lines[-1])
        self.assertIn('mean_us=3.0', self.lines[-1])

    def test_hour_of_flapping_emits_at_most_one_incident_and_total_per_thirty_seconds(self):
        for second in range(3600):
            self.stats.record(second * 1_000_000_000, 1000,
                              error=ValueError() if second % 2 == 0 else None)
        self.assertLessEqual(len(self.lines), 240)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
