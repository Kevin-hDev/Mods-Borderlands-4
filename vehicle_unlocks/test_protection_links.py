"""Restore only owned links, including partial writes, without overwriting foreign state."""
import struct
import sys
import unittest


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks.protection_links import Links
        except ImportError:
            self.fail('Transactional link owner missing')
        self.identity = ('stable',)
        self.values = {'Cello': (65536, struct.pack('<QQQ', 1, 2, 3)),
                       'Harp': (65568, struct.pack('<QQQ', 4, 2, 5))}
        self.original = dict(self.values)
        self.fail = None
        self.calls = []
        def capture():
            return self.identity, dict(self.values)
        def write(address, expected, value):
            key = next(k for k, pair in self.values.items() if pair[0] == address)
            self.assertEqual(self.values[key][1], expected)
            self.calls.append((key, value))
            if self.fail == key:
                self.fail = None
                self.values[key] = address, value[:4] + expected[4:]
                raise OSError('partial')
            self.values[key] = address, value
        self.links = Links(capture, write)

    def test_two_links_restore_independently(self):
        self.links.set(('Cello', 'Harp'))
        self.assertEqual(self.values['Cello'][1], bytes(8) + struct.pack('<Q', 2) + bytes(8))
        self.links.set(('Harp',))
        self.assertEqual(self.values['Cello'], self.original['Cello'])
        self.links.set(())
        self.assertEqual(self.values, self.original)

    def test_unloaded_original_is_restored_exactly_and_foreign_resolution_refused(self):
        from vehicle_unlocks.protection_links import Links
        self.values['Cello'] = 65536, struct.pack('<QQQ', 1, 2, 0)
        original = dict(self.values)
        links = Links(self.links.capture, self.links.write)
        links.set(('Cello',))
        links.set(())
        self.assertEqual(self.values, original)
        links.set(('Cello',))
        self.values['Cello'] = 65536, struct.pack('<QQQ', 0, 2, 123)
        before = len(self.calls)
        with self.assertRaises(RuntimeError):
            links.set(())
        self.assertEqual(len(self.calls), before)

    def test_partial_write_restores_every_touched_link(self):
        self.fail = 'Harp'
        with self.assertRaises(OSError):
            self.links.set(('Cello', 'Harp'))
        self.assertEqual(self.values, self.original)
        self.assertEqual(self.links.active, ())

    def test_foreign_link_is_not_overwritten(self):
        self.links.set(('Cello',))
        self.values['Cello'] = 65536, bytes([7]) * 24
        before = len(self.calls)
        with self.assertRaises(RuntimeError):
            self.links.set(())
        self.assertEqual(len(self.calls), before)

    def test_fact_or_catalogue_identity_change_refuses(self):
        self.links.set(('Cello',))
        self.identity = ('changed',)
        with self.assertRaises(RuntimeError):
            self.links.check()

    def test_duplicate_or_unknown_key_refuses(self):
        for keys in (('Cello', 'Cello'), ('Banjo',)):
            with self.assertRaises(ValueError):
                self.links.set(keys)
        self.assertEqual(self.calls, [])

    def test_restore_write_failure_keeps_previous_owned_state(self):
        self.links.set(('Cello', 'Harp'))
        before = dict(self.values)
        self.fail = 'Harp'
        with self.assertRaises(OSError):
            self.links.set(())
        self.assertEqual(self.values, before)
        self.assertEqual(self.links.active, ('Cello', 'Harp'))

    def test_rollback_failure_latches_restart_required(self):
        def broken(address, expected, value):
            self.values['Cello'] = address, bytes([7]) * 24
            raise OSError('partial foreign')
        self.links.write = broken
        with self.assertRaises(RuntimeError):
            self.links.set(('Cello',))
        self.assertTrue(self.links.failed)
        with self.assertRaises(RuntimeError):
            self.links.set(())


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
