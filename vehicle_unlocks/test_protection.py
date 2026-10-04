"""Shared ownership, persistence failures and restoration are observable contracts."""
import sys
import unittest


class Backend:
    def __init__(self):
        self.current = ()
        self.calls = []
        self.fail = False

    def set(self, keys):
        self.calls.append(keys)
        if self.fail:
            raise RuntimeError('unavailable')
        self.current = keys

    def check(self):
        if self.fail:
            raise RuntimeError('changed')


class Tests(unittest.TestCase):
    def setUp(self):
        try:
            from vehicle_unlocks.protection import Controller
        except ImportError:
            self.fail('Protection controller missing')
        self.saved, self.backend = (), Backend()
        self.fail_save = False
        def save(keys):
            if self.fail_save:
                raise OSError('disk')
            self.saved = keys
        self.c = Controller(lambda: self.saved, save, lambda: self.backend, lambda _: None)

    def test_boot_restores_requested_links_without_any_reward_call(self):
        self.saved = ('Cello',)
        self.assertTrue(self.c.start('save_editor'))
        self.assertEqual(self.backend.current, ('Cello',))
        self.assertTrue(self.c.start('vehicle_driving'))
        self.assertTrue(self.c.stop('save_editor'))
        self.assertEqual(self.backend.current, ('Cello',))
        self.assertTrue(self.c.stop('vehicle_driving'))
        self.assertEqual(self.backend.current, ())
        self.assertEqual(self.saved, ('Cello',))

    def test_only_explicit_request_is_saved_and_reenable_recovers_it(self):
        self.c.start('save_editor')
        self.assertEqual(self.backend.calls, [])
        self.c.request(('Cello',))
        self.assertEqual(self.saved, ('Cello',))
        self.c.stop('save_editor')
        self.c.start('save_editor')
        self.assertEqual(self.backend.current, ('Cello',))

    def test_failed_save_restores_previous_protection_and_never_grants(self):
        self.c.start('save_editor')
        self.fail_save = True
        with self.assertRaises(OSError):
            self.c.request(('Cello',))
        self.assertEqual(self.backend.current, ())
        self.assertEqual(self.saved, ())

    def test_restore_failure_retains_owner_and_blocks_requests(self):
        self.c.start('save_editor')
        self.c.request(('Cello',))
        self.backend.fail = True
        self.assertFalse(self.c.stop('save_editor'))
        self.assertIn('save_editor', self.c.owners)
        with self.assertRaises(RuntimeError):
            self.c.request(('Cello',))

    def test_invalid_saved_state_and_unknown_owners_do_not_write(self):
        self.saved = ('Banjo',)
        self.assertFalse(self.c.start('save_editor'))
        self.assertEqual(self.backend.calls, [])
        with self.assertRaises(ValueError):
            self.c.start('foreign')

    def test_request_requires_active_owner_and_rejects_bad_keys(self):
        with self.assertRaises(RuntimeError):
            self.c.request(('Cello',))
        self.c.start('save_editor')
        for keys in (('Cello', 'Cello'), ('Banjo',), ('Cello',) * 100, 'Cello'):
            with self.assertRaises(ValueError):
                self.c.request(keys)
        self.assertEqual(self.backend.calls, [])

    def test_failed_start_is_not_retried_by_second_owner_or_request(self):
        self.saved = ('Cello',)
        self.backend.fail = True
        self.assertFalse(self.c.start('save_editor'))
        calls = list(self.backend.calls)
        self.assertFalse(self.c.start('vehicle_driving'))
        with self.assertRaises(RuntimeError):
            self.c.request(('Cello',))
        self.assertEqual(self.backend.calls, calls)

    def test_startup_of_disabled_owner_is_not_needed_for_shared_request(self):
        self.c.start('vehicle_driving')
        self.c.request(('Cello', 'Harp'))
        self.assertTrue(self.c.stop('save_editor'))
        self.assertEqual(self.backend.current, ('Cello', 'Harp'))
        self.assertEqual(self.c.owners, {'vehicle_driving'})


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
