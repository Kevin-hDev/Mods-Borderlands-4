"""Startup observation is shared, bounded, cancelled on stop, and self-removing."""
import sys
import unittest
from types import SimpleNamespace as NS
from vehicle_unlocks import protection_config as cfg


class Tests(unittest.TestCase):
    def setUp(self):
        from vehicle_unlocks.protection_startup import Waiter
        self.now, self.calls, self.ready = 0, [], False
        def fail(error):
            self.c.pending = False
            self.calls.append(('failure', str(error)))
        def resume():
            self.calls.append('resume')
            self.c.pending = not self.ready
        self.c = NS(pending=True, resume=resume, fail=fail)
        self.w = Waiter(self.c, lambda: self.now, self.install, self.remove)

    def install(self, callback):
        self.calls.append('install')
        self.callback = callback

    def remove(self):
        self.calls.append('remove')

    def test_shared_wait_once_throttle_then_remove_when_ready(self):
        self.w.sync(); self.w.sync()
        self.assertEqual(self.calls, ['install'])
        self.callback()
        self.callback()
        self.assertEqual(self.calls, ['install', 'resume'])
        self.ready = True
        self.now += cfg.STARTUP_POLL_NS
        self.callback()
        self.assertEqual(self.calls[-2:], ['resume', 'remove'])
        self.assertFalse(self.w.active)

    def test_timeout_fails_without_retry_and_removes_hook(self):
        self.w.sync()
        self.now = cfg.STARTUP_TIMEOUT_NS
        self.callback()
        self.assertEqual(self.calls[-2:], [('failure', 'DLC catalogue startup timeout'), 'remove'])
        self.assertNotIn('resume', self.calls)

    def test_attempt_bound_and_stop_cancel(self):
        self.w.sync()
        self.w.attempts = cfg.STARTUP_MAX_ATTEMPTS
        self.callback()
        self.assertFalse(self.w.active)
        self.setUp()
        self.w.sync()
        self.c.pending = False
        self.w.sync()
        self.assertEqual(self.calls, ['install', 'remove'])

    def test_registration_and_removal_errors_are_not_ignored(self):
        def broken(*_):
            raise RuntimeError('private details')
        self.w.install = broken
        self.w.sync()
        self.assertEqual(self.calls, [('failure', 'Startup hook unavailable')])
        self.setUp()
        self.w.sync()
        self.w.remove = broken
        self.c.pending = False
        self.w.sync()
        self.assertEqual(self.calls[-1], ('failure', 'Startup hook unavailable'))


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
