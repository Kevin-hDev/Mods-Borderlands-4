"""Cold startup may wait only for the measured empty catalogue, without awards."""
import sys
import unittest
from types import SimpleNamespace
from vehicle_unlocks.protection import Controller
from vehicle_unlocks.protection_catalogue import CataloguePending


class Tests(unittest.TestCase):
    def setUp(self):
        self.ready = False
        self.calls, self.lines = [], []
        self.backend = SimpleNamespace(set=self.calls.append, check=lambda: None)
        def factory():
            if not self.ready:
                raise CataloguePending()
            return self.backend
        self.c = Controller(lambda: ('Cello',), self.fail_save, factory, self.lines.append)

    def fail_save(self, _):
        self.fail('Startup must never save or grant rewards')

    def test_empty_then_ready_with_two_owners_applies_once(self):
        self.assertFalse(self.c.start('save_editor'))
        self.assertTrue(self.c.pending)
        self.assertFalse(self.c.failed)
        self.assertFalse(self.c.start('vehicle_driving'))
        self.assertFalse(self.c.resume())
        self.ready = True
        self.assertTrue(self.c.resume())
        self.assertFalse(self.c.pending)
        self.assertEqual(self.calls, [('Cello',)])
        self.assertTrue(self.c.resume())
        self.assertEqual(self.calls, [('Cello',)])

    def test_last_owner_stops_wait_and_reenable_starts_again(self):
        self.c.start('save_editor')
        self.assertTrue(self.c.stop('save_editor'))
        self.assertFalse(self.c.pending)
        self.ready = True
        self.assertFalse(self.c.resume())
        self.assertEqual(self.calls, [])
        self.assertTrue(self.c.start('vehicle_driving'))
        self.assertEqual(self.calls, [('Cello',)])

    def test_real_failure_while_waiting_latches_and_blocks_requests(self):
        self.c.start('save_editor')
        def fail():
            raise ValueError('Native DLC contract differs')
        self.c.factory = fail
        self.assertFalse(self.c.resume())
        self.assertTrue(self.c.failed)
        self.assertFalse(self.c.pending)
        with self.assertRaises(RuntimeError):
            self.c.request(('Cello',))

    def test_pending_request_cannot_bypass_wait(self):
        self.c.start('save_editor')
        with self.assertRaises(RuntimeError):
            self.c.request(('Cello',))
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
