"""A historical receipt must not hide a revoked promotional vehicle."""
import sys
import unittest
from unittest.mock import Mock
from vehicle_unlocks import config


class Engine:
    def __init__(self, receipt=True):
        self.key = config.ACTIONS['promotions'][0].reward
        self.unique = ('Other', self.key) if receipt else ('Other',)
        self.pending = ()
        self.calls = []

    def snapshot(self):
        return self.unique, self.pending

    def write_unique(self, values):
        self.unique = values

    def give(self, target):
        self.calls.append('give')
        self.unique += (target.reward,)
        self.pending += (target.reward,)

    def validate(self, target):
        self.calls.append('validate')

    def open(self, target):
        self.calls.append('open')
        self.pending = ()


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks.promotion_award import apply
        except ImportError:
            self.fail('Promotional receipt repair missing')
        self.apply = apply
        self.target = config.ACTIONS['promotions'][0]

    def test_existing_receipt_does_not_skip_delivery(self):
        engine = Engine()
        result = self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(result.kind, 'delivered')
        self.assertEqual(result.changed, 1)
        self.assertEqual(engine.calls, ['give', 'validate', 'open'])
        self.assertEqual(engine.snapshot(), (('Other', engine.key), ()))

    def test_first_delivery_uses_same_native_route(self):
        engine = Engine(False)
        self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.snapshot(), (('Other', engine.key), ()))

    def test_failed_give_restores_receipt_and_is_uncertain(self):
        from vehicle_unlocks.batch import Uncertain
        engine = Engine()
        engine.give = Mock(side_effect=RuntimeError('delivery failed'))
        with self.assertRaises(Uncertain):
            self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.snapshot(), (('Other', engine.key), ()))
        engine.give.assert_called_once()

    def test_duplicate_receipt_refuses_before_any_change(self):
        engine = Engine()
        engine.unique += (engine.key,)
        with self.assertRaises(ValueError):
            self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.calls, [])

    def test_no_package_cannot_be_reported_as_delivered(self):
        from vehicle_unlocks.batch import Uncertain
        engine = Engine()
        engine.give = lambda _: None
        with self.assertRaises(Uncertain):
            self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.unique, ('Other', engine.key))

    def test_already_pending_target_is_opened_once_without_giving_again(self):
        engine = Engine()
        engine.pending = (engine.key,)
        self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.calls, ['validate', 'open'])

    def test_partial_receipt_set_failure_restores_target(self):
        from vehicle_unlocks.batch import Uncertain
        engine = Engine()
        def write(values):
            engine.unique = values
            if engine.key not in values:
                raise RuntimeError('assignment wrote then failed')
        engine.write_unique = write
        with self.assertRaises(Uncertain):
            self.apply(engine, (self.target,), lambda: None, lambda _: None)
        self.assertEqual(engine.unique, ('Other', engine.key))
        self.assertEqual(engine.calls, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
