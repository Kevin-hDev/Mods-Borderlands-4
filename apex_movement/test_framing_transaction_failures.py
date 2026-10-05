"""A failed framing transaction releases the real window without promising recovery."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

import movement_ui_fixture as sdk_fixture
sdk_fixture.install()
import apex_movement
from apex_movement import camera_settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from apex_movement import panel_preferences
from ads_panel_test_fixtures import AdsPanelTests


class Tests(unittest.TestCase):
    package = apex_movement
    settings = camera_settings
    build = AdsPanelTests.build

    def setUp(self):
        AdsPanelTests.setUp(self)
        self.settings.orbit.commit(False)
        for option in self.settings.framing.options:
            option.value = option.default_value
        self.now = [1]
        self.widgets, self.form = self.build()
        self.form.model.transaction.clock = lambda: self.now[0]
        self.original_save = self.package.mod.save_settings
        self.addCleanup(setattr, self.package.mod, "save_settings", self.original_save)
        self.original_confirm = self.settings.framing.confirm
        self.addCleanup(setattr, self.settings.framing, "confirm", self.original_confirm)

    def choose_zoom(self):
        self.widgets["framing:zoom:preset:2"].SetIsChecked(True)
        self.form.poll()
        return self.form.flush(self.widgets)

    def assert_failed_window_can_close(self, notice="rollback_abandoned"):
        self.assertFalse(self.form.model.transaction.pending, "Rollback still owns the window")
        self.assertEqual(self.form.notice, notice)
        text = self.widgets["notice"].calls["SetText"][0]
        self.assertNotIn("Previous settings kept", text)
        self.assertNotIn("private path", text)
        self.package.panel_preferences.french.value = True
        self.form.refresh_labels(self.widgets)
        french = self.widgets["notice"].calls["SetText"][0]
        self.assertNotIn("Réglages précédents conservés", french)
        self.assertNotIn("private path", french)
        self.assertTrue(self.form.close_ready())
        self.widgets["close"].SetIsChecked(True)
        self.assertTrue(self.form.poll())

    def test_repeated_native_refusal_eventually_releases_the_window(self):
        self.settings.framing.confirm = lambda _restoring=False: False
        self.assertFalse(self.choose_zoom())
        self.assertTrue(self.form.model.transaction.pending)
        self.assertFalse(self.form.close_ready())
        self.now[0] = 30_000_000_000
        self.form.poll()
        self.assert_failed_window_can_close()
        self.assertEqual(self.settings.framing.read("zoom"), (15, False))

    def test_repeated_save_failure_stops_retrying_after_compensation_budget(self):
        writes = []
        original_path = self.package.mod.settings_file
        self.addCleanup(setattr, self.package.mod, "settings_file", original_path)
        # Unknown persistence requires bounded retries; a proven unchanged file does not.
        self.package.mod.settings_file = None

        def fail_save():
            writes.append(self.settings.framing.snapshot())
            raise OSError("private path")

        self.package.mod.save_settings = fail_save
        self.assertFalse(self.choose_zoom())
        self.assertTrue(self.form.model.transaction.pending)
        self.now[0] = 3_000_000_001
        self.form.poll()
        self.assertTrue(self.form.model.transaction.pending)
        self.now[0] = 7_000_000_001
        self.form.poll()
        self.assert_failed_window_can_close("failed")
        self.assertEqual(len(writes), 4, "One write and three compensation attempts are permitted")
        self.now[0] = 100_000_000_000
        self.form.poll()
        self.assertEqual(len(writes), 4, "A completed failure cannot start writing again")

    def test_failed_open_window_shows_generic_save_failure_in_both_languages(self):
        writes = []
        mod = self.package.mod
        previous_path = getattr(mod, "settings_file", None)
        self.addCleanup(setattr, mod, "settings_file", previous_path)
        with tempfile.TemporaryDirectory() as folder:
            mod.settings_file = Path(folder) / "settings.json"
            mod.settings_file.write_text("original", encoding="utf-8")
            def fail_open():
                writes.append(True)
                raise PermissionError("private path")
            mod.save_settings = fail_open
            self.assertFalse(self.choose_zoom())
            self.assert_failed_window_can_close("failed")
            self.assertEqual(writes, [True])
            self.assertEqual(mod.settings_file.read_text(encoding="utf-8"), "original")
            self.assertEqual(self.settings.framing.read("zoom"), (15, False))
            self.package.panel_preferences.french.value = False
            self.form.refresh_labels(self.widgets)
            english = self.widgets["notice"].calls["SetText"][0]
            self.assertEqual(english, "Settings could not be saved. Please try again.")
            self.package.panel_preferences.french.value = True
            self.form.refresh_labels(self.widgets)
            self.assertEqual(self.widgets["notice"].calls["SetText"][0], "Impossible d’enregistrer les réglages. Réessaie.")

    def test_camera_timeout_window_announces_confirmed_restoration(self):
        self.settings.framing.confirm = lambda restoring=False: True if restoring else None
        self.assertFalse(self.choose_zoom())
        self.now[0] = 2_100_000_001
        self.form.poll()
        self.assertFalse(self.form.model.transaction.pending)
        self.assertEqual(self.form.notice, "camera_timeout")
        self.assertIn("Previous settings were restored", self.widgets["notice"].calls["SetText"][0])
        self.package.panel_preferences.french.value = True
        self.form.refresh_labels(self.widgets)
        self.assertIn("réglages précédents ont été rétablis", self.widgets["notice"].calls["SetText"][0])

    def test_unanswered_compensation_expires_but_waits_for_a_live_answer_first(self):
        confirmed = [False]
        self.settings.framing.confirm = lambda _restoring=False: confirmed[0]
        self.assertFalse(self.choose_zoom())
        confirmed[0] = None
        self.now[0] = 3_000_000_001
        self.form.poll()
        self.assertTrue(self.form.model.transaction.pending)
        self.assertFalse(self.form.close_ready())
        self.now[0] = 30_000_000_000
        self.form.poll()
        self.assert_failed_window_can_close()

    def test_live_confirmation_before_the_deadline_persists_the_selected_preset(self):
        confirmed = [None]
        self.settings.framing.confirm = lambda _restoring=False: confirmed[0]
        writes = []
        self.package.mod.save_settings = lambda: writes.append(self.settings.framing.snapshot())
        self.assertFalse(self.choose_zoom())
        self.now[0] = 1_000_000_000
        self.form.poll()
        self.assertTrue(self.form.model.transaction.pending)
        self.assertEqual(writes, [])
        confirmed[0] = True
        self.form.poll()
        self.assertFalse(self.form.model.transaction.pending)
        self.assertEqual(self.form.notice, "saved")
        self.assertEqual(writes, [((25, False), (10, False), (0, False))])

    def test_missing_optional_renderer_saves_a_dormant_preset(self):
        camera = self.package.camera
        controller = NS(_bridge_started=True, _in_vehicle=False, _aiming=False,
                        _aim_returning=False, _desired_mode="ThirdPerson", framing=None)
        runtime = NS(arbiter=NS(active=lambda: NS(owner=camera.OWNER)), third_person=controller)
        self.settings.framing.confirm = lambda restoring=False: camera.confirm_settings(
            runtime, camera.OWNER, camera.ADAPTER, restoring)
        writes = []
        self.package.mod.save_settings = lambda: writes.append(self.settings.framing.snapshot())
        self.assertTrue(self.choose_zoom(), "Optional framing absence must preserve the dormant choice")
        self.assertFalse(self.form.model.transaction.pending)
        self.assertEqual(self.settings.framing.read("zoom"), (25, False))
        self.assertEqual(writes, [((25, False), (10, False), (0, False))])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
