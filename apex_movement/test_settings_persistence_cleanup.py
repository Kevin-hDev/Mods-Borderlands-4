"""Crash cleanup is bounded, attributable, and never deletes a live writer's file."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from settings_persistence_test_fixtures import PersistenceCase


CHILD = """
import os, sys
from pathlib import Path
path = Path(sys.argv[1])
temporary = path.with_name(f'{path.name}.{os.getpid():08x}' + '1' * 32 + '.tmp')
temporary.write_text('{"incomplete":')
print(temporary.name, flush=True)
if sys.argv[2] == 'active':
    sys.stdin.readline()
os._exit(23)
"""
SDK_CRASH = """
import os, sys
from pathlib import Path
import movement_ui_fixture
movement_ui_fixture.install()
from apex_movement.settings_persistence import AtomicSettingsMixin
class SDK:
    def save_settings(self):
        self.settings_file.write_text('{"incomplete":')
        os._exit(23)
class Mod(AtomicSettingsMixin, SDK):
    pass
mod = Mod()
mod.settings_file = Path(sys.argv[1])
mod.save_settings()
"""


class Tests(PersistenceCase):
    def child(self, active=False):
        command = [sys.executable, "-c", CHILD, str(self.path), "active" if active else "crash"]
        if active:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            self.addCleanup(process.communicate, "release\n", timeout=5)
            name = process.stdout.readline().strip()
        else:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 23)
            name = result.stdout.strip()
        self.assertTrue(name.startswith("settings.json."))
        return self.path.parent / name

    def test_temporaries_include_mod_name_and_live_owner(self):
        dump = json.dump
        names = []
        def recording(values, target):
            names.append(Path(target.name).name)
            return dump(values, target)
        with patch("json.dump", recording):
            self.save_successfully()
        self.assertRegex(names[0], rf"^settings\.json\.{os.getpid():08x}[0-9a-f]{{32}}\.tmp$")

    def test_first_sdk_save_removes_a_proven_crashed_writer_only(self):
        orphan = self.child()
        neighbours = (self.path.parent / ("2" * 32 + ".tmp"),
                      self.path.parent / ("another.json." + orphan.name.split(".")[2] + ".tmp"),
                      self.path.parent / ("settings.json." + "x" * 40 + ".tmp"))
        for neighbour in neighbours:
            neighbour.write_text("other")
        self.save_successfully()
        self.assertFalse(orphan.exists())
        for neighbour in neighbours:
            self.assertTrue(neighbour.is_file())
            self.assertEqual(neighbour.read_text(), "other")
        self.assertTrue(self.path.is_file())
        self.assertEqual(json.loads(self.path.read_text()), {"new": True})

    def test_killed_sdk_writer_leaves_old_bytes_and_is_cleaned_on_next_startup(self):
        result = subprocess.run([sys.executable, "-c", SDK_CRASH, str(self.path)],
                                cwd=Path(__file__).parent, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.path.read_text(), '{"old": true}')
        remnants = [entry for entry in self.path.parent.iterdir() if entry != self.path]
        self.assertEqual(len(remnants), 1)
        self.assertTrue(remnants[0].name.startswith("settings.json."))
        self.save_successfully()
        self.assertFalse(remnants[0].exists())

    def test_another_process_active_temporary_survives_startup_cleanup(self):
        active = self.child(active=True)
        self.save_successfully()
        self.assertTrue(active.is_file())
        self.assertEqual(active.read_text(), '{"incomplete":')

    def test_current_process_temporary_and_nonregular_entries_are_never_removed(self):
        live = self.path.with_name(f"settings.json.{os.getpid():08x}" + "3" * 32 + ".tmp")
        live.write_text("active")
        directory = self.child()
        directory.unlink()
        directory.mkdir()
        self.save_successfully()
        self.assertTrue(live.is_file())
        self.assertEqual(live.read_text(), "active")
        self.assertTrue(directory.is_dir())

    def test_cleanup_is_bounded_and_runs_once_per_mod_instance(self):
        scanned = []
        scandir = os.scandir
        class Scan:
            def __enter__(scan):
                scan.iterator = scandir(self.path.parent)
                return scan
            def __iter__(scan):
                for entry in scan.iterator:
                    scanned.append(entry.name)
                    yield entry
            def __exit__(scan, *_args):
                scan.iterator.close()
        for number in range(140):
            (self.path.parent / f"other-{number}").touch()
        with patch.object(self.persistence.os, "scandir", return_value=Scan()):
            self.save_successfully()
            first = len(scanned)
            self.save_successfully()
        self.assertGreater(first, 0)
        self.assertLessEqual(first, 128)
        self.assertEqual(len(scanned), first)

    def test_cleanup_cannot_follow_an_owned_name_symlink(self):
        orphan = self.child()
        orphan.unlink()
        target = self.path.parent / "other-data"
        target.write_text("keep")
        try:
            orphan.symlink_to(target)
        except OSError as error:
            if os.name == "nt" and error.winerror == 1314:
                self.skipTest("Creating Windows symlinks requires a privilege")
            raise
        self.save_successfully()
        self.assertTrue(orphan.is_symlink())
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_text(), "keep")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
