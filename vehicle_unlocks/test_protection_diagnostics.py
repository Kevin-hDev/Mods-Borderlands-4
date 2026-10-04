"""Startup errors retain their cause without leaking arbitrary exception text."""
import sys
import unittest
from vehicle_unlocks.protection import Controller


class Tests(unittest.TestCase):
    def test_first_failure_has_stable_reason_and_survives_second_owner(self):
        lines = []
        def fail():
            raise ValueError('Original vehicle reward differs')
        controller = Controller(lambda: ('Cello',), lambda _: None, fail, lines.append)
        self.assertFalse(controller.start('save_editor'))
        self.assertFalse(controller.start('vehicle_driving'))
        self.assertIn('code=reward_reference', lines[0])
        self.assertIn('code=reward_reference', lines[1])

    def test_unknown_error_text_and_paths_are_not_logged(self):
        lines = []
        def fail():
            raise ValueError('secret_token=C:/private/personal')
        controller = Controller(lambda: ('Cello',), lambda _: None, fail, lines.append)
        self.assertFalse(controller.start('save_editor'))
        self.assertIn('code=unknown', lines[0])
        self.assertNotIn('private', lines[0])
        self.assertNotIn('secret', lines[0])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
