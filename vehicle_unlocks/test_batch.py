"""Reward batches must preserve unrelated rewards and never retry ambiguous writes."""
import sys
import unittest
from types import SimpleNamespace as NS


class Engine:
    def __init__(self, unique=(), pending=()):
        self.unique, self.pending = tuple(unique), tuple(pending)
        self.calls = []
        self.packaged = set()
        self.fail = self.extra = False

    def snapshot(self):
        return self.unique, self.pending

    def validate(self, target):
        self.calls.append(('validate', target.reward))

    def give(self, target):
        self.calls.append(('give', target.reward))
        if self.fail:
            raise RuntimeError('unknown native outcome')
        if target.reward in self.packaged:
            self.pending += (target.reward,)
        else:
            self.unique += (target.reward,)
        if self.extra:
            self.unique += ('UnrelatedReward',)

    def open(self, target):
        self.calls.append(('open', target.reward))
        index = self.pending.index(target.reward)
        self.pending = self.pending[:index] + self.pending[index + 1:]
        if target.reward not in self.unique:
            self.unique += (target.reward,)


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks import batch, config
        except ImportError:
            self.fail('Shared vehicle unlock implementation is missing')
        self.batch, self.cfg = batch, config
        self.targets = self.cfg.ACTIONS['standard']
        self.engine = Engine(('Other',), ('OtherPackage',))

    def apply(self, targets=None, guard=lambda: None):
        return self.batch.apply(self.engine, targets or self.targets, guard, lambda _: None)

    def test_three_disjoint_actions_have_explicit_contents(self):
        self.assertEqual(tuple(self.cfg.ACTIONS), ('standard', 'promotions', 'shatterland'))
        self.assertEqual(len(self.targets), 10)
        self.assertEqual(len({item.reward for group in self.cfg.ACTIONS.values() for item in group}), 15)
        promos = self.cfg.ACTIONS['promotions']
        self.assertEqual([(item.reward, item.contents) for item in promos], [
            ('RewardPackage_CelloVehicle', (('GbxRewardData_Unlockable', 'Unlockable_Vehicles.Mountain'),)),
            ('RewardPackage_MandolinVehicle', (('GbxRewardData_Unlockable', 'Unlockable_Vehicles.CityOrder'),)),
            ('RewardPackage_HarpVehicle', (('GbxRewardData_Unlockable', 'Unlockable_Vehicles.ShatterlandV2'),)),
            ('RewardPackage_ViolaVehicle', (('GbxRewardData_Unlockable', 'Unlockable_Vehicles.Stingray'),)),
        ])
        shatter, = self.cfg.ACTIONS['shatterland']
        self.assertEqual(shatter.contents, (('GbxRewardData_UnlockableLedger', 'Unlockable_BanjoDLC'),
                                          ('GbxRewardData_Unlockable', 'Unlockable_Vehicles.ShatterlandV1')))

    def test_direct_and_packaged_rewards_preserve_unrelated_state(self):
        self.engine.packaged = {item.reward for item in self.targets[::2]}
        result = self.apply()
        self.assertEqual((result.changed, result.skipped), (10, 0))
        self.assertEqual(self.engine.pending, ('OtherPackage',))
        self.assertEqual(set(self.engine.unique), {'Other', *(item.reward for item in self.targets)})
        self.assertEqual(sum(key == 'open' for key, _ in self.engine.calls), 5)

    def test_received_rewards_are_not_given_again(self):
        self.engine.unique += tuple(item.reward for item in self.targets)
        result = self.apply()
        self.assertEqual((result.changed, result.skipped), (0, 10))
        self.assertFalse(self.engine.calls)

    def test_pending_reward_is_opened_without_regrant_even_when_unique(self):
        target = self.targets[0]
        self.engine.unique += (target.reward,)
        self.engine.pending += (target.reward,)
        result = self.apply((target,))
        self.assertEqual(result.changed, 1)
        self.assertNotIn(('give', target.reward), self.engine.calls)
        self.assertEqual(self.engine.pending, ('OtherPackage',))

    def test_duplicate_pending_reward_refuses_before_any_write(self):
        self.engine.pending += (self.targets[-1].reward,) * 2
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse(any(call[0] in ('give', 'open') for call in self.engine.calls))

    def test_context_change_before_first_write_is_not_uncertain(self):
        def guard():
            raise ValueError('context changed')
        with self.assertRaises(ValueError):
            self.apply(guard=guard)
        self.assertFalse(self.engine.calls)

    def test_native_failure_stops_batch_as_uncertain_without_retry(self):
        self.engine.fail = True
        with self.assertRaises(self.batch.Uncertain):
            self.apply()
        self.assertEqual(sum(key == 'give' for key, _ in self.engine.calls), 1)

    def test_unrelated_mutation_stops_batch(self):
        self.engine.extra = True
        with self.assertRaises(self.batch.Uncertain):
            self.apply()
        self.assertEqual(sum(key == 'give' for key, _ in self.engine.calls), 1)

    def test_empty_or_oversized_batch_refuses(self):
        for targets in ((), self.targets + self.targets):
            with self.assertRaises(ValueError):
                self.batch.apply(self.engine, targets, lambda: None, lambda _: None)
        self.assertFalse(self.engine.calls)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
