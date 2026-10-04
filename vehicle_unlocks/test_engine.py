"""Reflection contracts and exact reward contents gate package opening."""
import sys
import unittest
from types import SimpleNamespace as NS


def reference(label, kind='GbxRewardsDef', address=1, **fields):
    return NS(_name=label, _type=NS(Name=kind), _get_address=lambda: address, **fields)


class Tests(unittest.TestCase):
    def test_receipt_assignment_is_bounded_and_read_back(self):
        from vehicle_unlocks.engine import Engine
        engine = Engine.__new__(Engine)
        engine.manager = NS(UniqueRewards=['Other'])
        engine.write_unique(('Other', 'RewardPackage_CelloVehicle'))
        self.assertEqual(engine.manager.UniqueRewards, ['Other', 'RewardPackage_CelloVehicle'])
        for values in (('bad/path',), ('Other',) * 2049):
            with self.assertRaises(ValueError):
                engine.write_unique(values)

    def setUp(self):
        try:
            from vehicle_unlocks import engine, config
        except ImportError:
            self.fail('Reward engine implementation is missing')
        self.module, self.cfg = engine, config
        self.target = config.ACTIONS['shatterland'][0]
        self.items = [NS(_type=NS(Name=kind), **{
            'UnlockableLedgerDef' if 'Ledger' in kind else 'UnlockableDef': reference(label, 'UnlockableEntryDef')
        }) for kind, label in self.target.contents]
        self.ref = reference(self.target.reward, reward=NS(
            bIsUnique=True, UniqueName=self.target.reward, rewarddata=self.items))

    def test_full_promotional_bundle_accepts_exact_two_items(self):
        self.module.validate_definition(self.ref, self.target)

    def test_extra_or_wrong_unlockable_is_rejected(self):
        for items in (self.items[:1], self.items + self.items, self.items[::-1]):
            self.ref.reward.rewarddata = items
            with self.assertRaises(ValueError):
                self.module.validate_definition(self.ref, self.target)

    def test_wrong_type_unresolved_and_non_unique_refuse(self):
        for ref in (reference(self.target.reward, address=0), reference('Other'),
                    reference(self.target.reward, 'OtherType')):
            with self.assertRaises(ValueError):
                self.module.validate_definition(ref, self.target)
        self.ref.reward.bIsUnique = False
        with self.assertRaises(ValueError):
            self.module.validate_definition(self.ref, self.target)

    def test_collections_are_bounded_and_names_validated(self):
        for values, bound in ((['Valid'] * 65, 64), (['unsafe/name'], 64), ([1], 64)):
            with self.assertRaises(ValueError):
                self.module.labels(values, bound)
        self.assertEqual(self.module.labels(['SomeReward'], 64), ('SomeReward',))

    def test_signature_requires_exact_names_types_and_count(self):
        prop = NS(Name='PackageIndex', Class=NS(Name='IntProperty'))
        func = NS(NumParams=1, _properties=lambda: iter((prop,)))
        bound = NS(func=func)
        with self.assertRaises(ValueError):
            self.module.check_function(bound, self.cfg.OPEN_PARAMETERS)
        def function(*args):
            self.fail('Contract check invoked a game function')
        function.func = func
        self.assertIs(self.module.check_function(function, self.cfg.OPEN_PARAMETERS), function)
        prop.Name = 'Unexpected'
        with self.assertRaises(ValueError):
            self.module.check_function(function, self.cfg.OPEN_PARAMETERS)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
