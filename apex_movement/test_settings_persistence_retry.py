"""Only transient Windows sharing locks earn a short, bounded replacement retry."""
import errno
import json
import os
import stat
import unittest
from unittest.mock import patch

from settings_persistence_test_fixtures import PersistenceCase, WindowsReader


class Tests(PersistenceCase):
    def reader(self):
        reader = WindowsReader(self.path)
        self.addCleanup(reader.close)
        return reader

    def test_reader_released_during_retry_commits_the_sdk_bytes(self):
        reader = self.reader()
        delays = []
        def release(delay):
            delays.append(delay)
            reader.close()
        with patch("time.sleep", release):
            self.save_successfully()
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(len(delays), 1)
        self.assertLessEqual(sum(delays), 0.02)
        self.assertEqual(self.mod.settings_file, self.path)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_permanent_reader_stops_after_three_attempts_preserving_old_bytes(self):
        self.reader()
        attempts, delays = [], []
        replace = os.replace
        def recording(*args):
            attempts.append(args)
            return replace(*args)
        with patch.object(self.persistence.os, "replace", recording), patch("time.sleep", delays.append):
            with self.assertRaises(PermissionError):
                self.mod.save_settings()
        self.assertEqual(len(attempts), 3)
        self.assertEqual(len(delays), 2)
        self.assertLessEqual(sum(delays), 0.02)
        self.assert_intact()

    def test_reader_of_temporary_file_can_release_during_retry(self):
        dump = json.dump
        readers = []
        def lock_after_write(values, target):
            dump(values, target)
            reader = WindowsReader(target.name)
            readers.append(reader)
            self.addCleanup(reader.close)
        def release(_delay):
            readers[0].close()
        with patch("json.dump", lock_after_write), patch("time.sleep", release):
            self.save_successfully()
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    @unittest.skipUnless(os.name == "nt", "Windows permissions are unavailable")
    def test_read_only_file_is_not_misclassified_as_a_transient_reader(self):
        os.chmod(self.path, stat.S_IREAD)
        self.addCleanup(os.chmod, self.path, stat.S_IREAD | stat.S_IWRITE)
        delays = []
        with patch("time.sleep", delays.append):
            with self.assertRaises(PermissionError):
                self.mod.save_settings()
        self.assertEqual(delays, [])
        self.assert_intact()

    def test_non_lock_replace_errors_do_not_wait_or_lose_previous_settings(self):
        for code in (errno.ENOSPC, errno.ENOENT, errno.EACCES):
            delays = []
            with self.subTest(code=code), patch("time.sleep", delays.append):
                with patch.object(self.persistence.os, "replace", side_effect=OSError(code, "synthetic")):
                    with self.assertRaises(OSError):
                        self.mod.save_settings()
            self.assertEqual(delays, [])
            self.assert_intact()

    def test_disk_full_during_sdk_write_never_replaces_the_previous_settings(self):
        def full(_values, target):
            target.write('{"partial":')
            raise OSError(errno.ENOSPC, "synthetic")
        with patch("json.dump", full), patch.object(self.persistence.os, "replace") as replace:
            with self.assertRaises(OSError):
                self.mod.save_settings()
        replace.assert_not_called()
        self.assert_intact()


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
