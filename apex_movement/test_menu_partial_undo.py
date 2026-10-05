"""The real window explains Undo's lost camera half in both languages."""
import unittest
import movement_ui_fixture
movement_ui_fixture.install()
import apex_movement
from apex_movement import camera_settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from apex_movement import settings
from ads_panel_test_fixtures import AdsPanelTests


class Tests(unittest.TestCase):
    package = apex_movement
    settings = camera_settings
    build = AdsPanelTests.build

    def test_partial_undo_is_visible_and_never_replayed_after_owner_returns(self):
        camera = self.package.camera
        original = camera.elected_elsewhere
        current = [False]
        camera.elected_elsewhere = lambda: current[0]
        self.addCleanup(setattr, camera, "elected_elsewhere", original)
        for language, expected in (("EN", "except the camera"), ("FR", "sauf la caméra")):
            with self.subTest(language=language):
                AdsPanelTests.setUp(self)
                self.settings.orbit.commit(False)
                self.settings.shoulder_left.commit(False)
                settings.dash.value = False
                current[0] = False
                widgets, form = self.build()
                self.package.panel_preferences.french.value = language == "FR"
                widgets["restore"].SetIsChecked(True)
                form.poll()
                self.assertEqual(form.notice, "restored")
                self.assertTrue(settings.dash.value)
                self.assertFalse(self.settings.third_person.value)
                current[0] = True
                widgets["undo"].SetIsChecked(True)
                form.poll()
                self.assertFalse(settings.dash.value)
                self.assertFalse(self.settings.third_person.value)
                self.assertEqual(form.notice, "undone_partial")
                self.assertIn(expected, widgets["notice"].calls["SetText"][0])
                self.assertFalse(form.model.can_undo)
                current[0] = False
                form.poll()
                self.assertFalse(self.settings.third_person.value)
                self.assertFalse(form.model.can_undo)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
