"""A fully released catalogue may resolve or move before the next activation."""
import itertools
import struct
import sys
import unittest

from vehicle_unlocks.protection import Controller
from vehicle_unlocks.protection_links import Links


OWNERS = ('save_editor', 'vehicle_driving')


class Tests(unittest.TestCase):
    def setUp(self):
        self.values = {'Cello': (65536, struct.pack('<QQQ', 1, 2, 0))}
        self.backends, self.writes = [], []
        self.invalid = False
        self.c = Controller(lambda: ('Cello',), self.no_save, self.factory, lambda _: None)

    def no_save(self, _):
        self.fail('Activation must not save a selection or distribute a reward')

    def factory(self):
        if self.invalid:
            raise ValueError('Native DLC contract differs')
        backend = Links(lambda: ('catalogue', dict(self.values)), self.write)
        self.backends.append(backend)
        return backend

    def write(self, address, expected, value):
        self.assertEqual(self.values['Cello'], (address, expected))
        self.writes.append(value)
        self.values['Cello'] = address, value

    def test_repeated_cycles_in_both_owner_orders_recapture_resolved_links(self):
        for stop_order, start_order in itertools.product(
                itertools.permutations(OWNERS), repeat=2):
            with self.subTest(stop=stop_order, start=start_order):
                self.setUp()
                for owner in OWNERS:
                    self.assertTrue(self.c.start(owner))
                for cycle in range(3):
                    previous = self.c.backend
                    self.assertTrue(self.c.stop(stop_order[0]))
                    self.assertIs(self.c.backend, previous)
                    self.c.check()
                    self.assertTrue(self.c.stop(stop_order[1]))
                    # The game can resolve its restored link while both mods are off.
                    original = (65536 + cycle * 32, struct.pack('<QQQ', 1, 2, cycle + 9))
                    self.values['Cello'] = original
                    for owner in start_order:
                        self.assertTrue(self.c.start(owner))
                    self.c.check()
                    self.assertEqual(len(self.backends), cycle + 2)
                    self.assertEqual(self.c.backend.original['Cello'], original)
                for owner in stop_order:
                    self.assertTrue(self.c.stop(owner))
                self.assertEqual(self.values['Cello'], original)

    def test_remaining_owner_never_accepts_changed_protected_link(self):
        for owner in OWNERS:
            self.assertTrue(self.c.start(owner))
        self.assertTrue(self.c.stop(OWNERS[0]))
        self.values['Cello'] = 65536, struct.pack('<QQQ', 1, 2, 9)
        before = len(self.writes)
        self.assertFalse(self.c.start(OWNERS[0]))
        self.assertEqual(len(self.backends), 1)
        self.assertEqual(len(self.writes), before)
        self.assertTrue(self.c.failed)

    def test_failed_restore_keeps_backend_and_owner_and_blocks_reactivation(self):
        self.assertTrue(self.c.start(OWNERS[0]))
        backend = self.c.backend
        self.values['Cello'] = 65536, bytes([7]) * 24
        before = len(self.writes)
        self.assertFalse(self.c.stop(OWNERS[0]))
        self.assertIs(self.c.backend, backend)
        self.assertEqual(self.c.owners, {OWNERS[0]})
        self.assertFalse(self.c.start(OWNERS[1]))
        self.assertEqual(len(self.writes), before)
        self.assertEqual(len(self.backends), 1)

    def test_new_activation_revalidates_native_contract_before_writing(self):
        self.assertTrue(self.c.start(OWNERS[0]))
        self.assertTrue(self.c.stop(OWNERS[0]))
        self.invalid = True
        before = len(self.writes)
        self.assertFalse(self.c.start(OWNERS[1]))
        self.assertTrue(self.c.failed)
        self.assertEqual(len(self.writes), before)

    def test_releasing_after_failure_does_not_clear_restart_requirement(self):
        self.assertTrue(self.c.start(OWNERS[0]))
        self.c.fail(RuntimeError('Protection state changed'))
        self.assertTrue(self.c.stop(OWNERS[0]))
        before = len(self.writes)
        self.assertFalse(self.c.start(OWNERS[1]))
        self.assertTrue(self.c.failed)
        self.assertEqual(len(self.writes), before)
        self.assertEqual(len(self.backends), 1)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
