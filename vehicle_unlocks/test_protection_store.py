"""One settings authority with bounded input and atomic replacement."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch


class Tests(unittest.TestCase):
    def test_round_trip_missing_and_invalid_state(self):
        try:
            from vehicle_unlocks import protection_store as store
        except ImportError:
            self.fail('Shared settings store missing')
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            with patch.object(store, 'path', return_value=path):
                self.assertEqual(store.load(), ())
                store.save(('Cello', 'Harp'))
                self.assertEqual(store.load(), ('Cello', 'Harp'))
                for raw in ('{}', '{"schema":1,"selected":["Banjo"]}', 'x' * 1025):
                    path.write_text(raw)
                    with self.assertRaises(ValueError):
                        store.load()

    def test_replace_failure_preserves_original(self):
        from vehicle_unlocks import protection_store as store
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            with patch.object(store, 'path', return_value=path):
                store.save(('Cello',))
                before = path.read_bytes()
                with patch.object(store.os, 'replace', side_effect=OSError('disk')):
                    with self.assertRaises(OSError):
                        store.save(('Cello', 'Harp'))
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(list(Path(folder).iterdir()), [path])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
