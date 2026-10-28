"""Real native process-access denial and temporary-file sharing locks stay fail closed."""
import ctypes
import json
import os
import unittest
from unittest.mock import patch

from settings_persistence_test_fixtures import PersistenceCase, WindowsReader


@unittest.skipUnless(os.name == "nt", "Windows native sharing and process identities are unavailable")
class Tests(PersistenceCase):
    def test_real_denied_process_inspection_cannot_make_its_temporary_an_orphan(self):
        api = self.persistence._WINDOWS
        handle = api.OpenProcess(0x100000, False, 4)
        if handle:
            self.assertTrue(api.CloseHandle(handle))
            self.skipTest("This account can inspect the protected System process")
        self.assertEqual(ctypes.get_last_error(), 5)
        temporary = self.path.with_name("settings.json.00000004" + "a" * 32 + ".tmp")
        temporary.write_text("protected owner")
        self.save_successfully()
        self.assertTrue(temporary.is_file(), "Denied inspection must keep the owner's temporary")
        self.assertEqual(temporary.read_text(), "protected owner")
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        if __name__ == "__main__":
            print("OBSERVED NATIVE WINDOWS IDENTITY: OpenProcess(System) denied, error=5; temporary kept")

    def temporary_reader(self, readers):
        dump = json.dump
        def lock_after_write(values, target):
            dump(values, target)
            reader = WindowsReader(target.name)
            readers.append(reader)
            self.addCleanup(reader.close)
        return patch("json.dump", lock_after_write)

    def test_real_brief_delete_lock_on_temporary_is_retried_before_commit(self):
        readers, delays = [], []
        def release(delay):
            delays.append(delay)
            readers[0].close()
        with self.temporary_reader(readers), patch("time.sleep", release):
            self.save_successfully()
        self.assertEqual(len(delays), 1)
        self.assertLessEqual(sum(delays), 0.02)
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_real_persistent_temporary_delete_lock_preserves_old_json_after_three_attempts(self):
        readers, delays, attempts = [], [], []
        replace = os.replace
        def recording(*args):
            attempts.append(True)
            return replace(*args)
        with self.temporary_reader(readers), patch("time.sleep", delays.append):
            with patch.object(self.persistence.os, "replace", recording):
                self.save_failing(PermissionError)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(len(delays), 2)
        self.assertLessEqual(sum(delays), 0.02)
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.path.read_text(), '{"old": true}')
        self.assertEqual(self.mod.settings_file, self.path)
        self.assertFalse(self.mod._settings_save_active)
        # The live reader also denies failed-save unlink; close it before test-folder teardown.
        readers[0].close()
        remaining = [entry for entry in self.path.parent.iterdir() if entry != self.path]
        self.assertEqual(len(remaining), 1)
        self.assertTrue(remaining[0].name.startswith("settings.json."))

    def test_access_denied_replace_with_real_temporary_lock_uses_temporary_probe(self):
        readers, native_codes, delays = [], [], []
        replace = os.replace
        def antivirus_denial(*args):
            try:
                return replace(*args)
            except PermissionError as error:
                native_codes.append(error.winerror)
                # This host returns 32 for a locked source; emulate a filter driver's 5 at the syscall boundary.
                denied = PermissionError("controlled access denial")
                denied.winerror = 5
                raise denied from None
        def release(delay):
            delays.append(delay)
            readers[0].close()
        with self.temporary_reader(readers), patch("time.sleep", release):
            with patch.object(self.persistence.os, "replace", antivirus_denial):
                self.save_successfully()
        self.assertEqual(native_codes, [32])
        self.assertEqual(len(delays), 1)
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        if __name__ == "__main__":
            print("OBSERVED TEMPORARY LOCK: native replace=32, adapted replace=5; native DELETE probe, retry committed")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
