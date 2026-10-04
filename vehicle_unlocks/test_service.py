"""A single shared owner serializes both mods and locks ambiguous outcomes."""
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks import service, batch
        except ImportError:
            self.fail('Shared vehicle service is missing')
        self.s, self.batch = service, batch
        tracing = patch.object(service, 'trace', lambda message: None)
        tracing.start()
        self.addCleanup(tracing.stop)
        service.locked = service.busy = False
        self.mod = NS(is_enabled=True)

    def test_disabled_busy_locked_invalid_actions_never_make_engine(self):
        with patch.object(self.s, 'context') as context, patch.object(self.s, 'engine_for') as engine:
            self.mod.is_enabled = False
            self.assertEqual(self.s.run('standard', self.mod).reason, 'disabled')
            self.mod.is_enabled = True
            self.s.busy = True
            self.assertEqual(self.s.run('standard', self.mod).reason, 'busy')
            self.s.busy, self.s.locked = False, True
            self.assertEqual(self.s.run('standard', self.mod).reason, 'restart')
            self.s.locked = False
            self.assertEqual(self.s.run('unsafe', self.mod).reason, 'unreadable')
            self.assertEqual(self.s.run([], self.mod).reason, 'unreadable')
            context.assert_not_called()
            engine.assert_not_called()

    def test_uncertain_batch_locks_next_mod_without_repeating(self):
        with patch.object(self.s, 'context', return_value=(1, 2, 3)), \
                patch.object(self.s, 'engine_for', return_value=object()), \
                patch.object(self.batch, 'apply', side_effect=self.batch.Uncertain(2, 1)) as apply:
            result = self.s.run('standard', self.mod)
            self.assertEqual((result.kind, result.changed), ('uncertain', 2))
            other_mod = NS(is_enabled=True)
            self.assertEqual(self.s.run('promotions', other_mod).reason, 'restart')
            apply.assert_called_once()
        self.assertFalse(self.s.busy)

    def test_preflight_refusal_does_not_lock_or_leak_details(self):
        with patch.object(self.s, 'context', side_effect=self.s.Refused('vehicle')):
            self.assertEqual(self.s.run('standard', self.mod).reason, 'vehicle')
        with patch.object(self.s, 'context', side_effect=RuntimeError('private user path')):
            result = self.s.run('standard', self.mod)
            self.assertEqual(result.reason, 'unreadable')
            self.assertNotIn('private', str(result))
        self.assertFalse(self.s.locked)

    def test_all_actions_pass_their_own_targets_and_same_guard(self):
        captured = []
        def apply(engine, targets, guard, trace):
            guard()
            captured.append(targets)
            return self.batch.Result('unchanged', skipped=len(targets))
        with patch.object(self.s, 'context', return_value=(1, 2, 3)), \
                patch.object(self.s, 'engine_for', return_value=object()), patch.object(self.batch, 'apply', apply):
            for action in ('standard', 'shatterland'):
                self.assertEqual(self.s.run(action, self.mod).kind, 'unchanged')
        self.assertEqual(list(map(len, captured)), [10, 1])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
