"""Camera presets exercised on this mod's actual generated window."""
import unittest
import movement_ui_fixture as sdk_fixture
sdk_fixture.install()
import apex_movement
from apex_movement import camera_settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from apex_movement import panel_preferences
from framing_panel_test_fixtures import FramingPanelTests


class Tests(FramingPanelTests, unittest.TestCase):
    package = apex_movement
    settings = camera_settings

    def test_dormant_framing_save_mentions_the_unavailable_preview(self):
        from unittest.mock import patch
        with patch.object(self.package.camera, "framing_status", return_value="unavailable"):
            widgets, form = self.build()
            widgets["framing:zoom:preset:2"].SetIsChecked(True)
            form.poll()
            self.assertTrue(form.flush(widgets))
            self.assertEqual(self.settings.framing.read("zoom"), (25, False))
            self.assertIn("preview", widgets["notice"].calls["SetText"][0].lower())

    def test_preview_notices_do_not_promise_that_a_refused_draft_is_kept(self):
        from unittest.mock import patch
        with patch.object(self.package.camera, "framing_status", return_value="unavailable"):
            widgets, form = self.build()
            self.assertNotIn("Your choice is kept", widgets["group:framing:zoom"].calls["SetText"][0])
            form.model.change_language("FR")
            form.refresh_labels(widgets)
            self.assertNotIn("Ton choix est gardé", widgets["group:framing:zoom"].calls["SetText"][0])

    def test_partial_preview_describes_only_the_refused_component(self):
        from unittest.mock import patch
        with patch.object(self.package.camera, "framing_status", return_value="zoom_unavailable"):
            widgets, form = self.build()
            message = widgets["group:framing:horizontal"].calls["SetText"][0]
            self.assertIn("Additional aiming zoom unavailable", message)
            self.assertNotIn("usual framing", message)
        with patch.object(self.package.camera, "framing_status", return_value="position_unavailable"):
            form.refresh_labels(widgets)
            message = widgets["group:framing:zoom"].calls["SetText"][0]
            self.assertIn("Camera position unavailable", message)
            self.assertNotIn("usual framing", message)

    def test_camera_refusal_is_not_presented_as_a_disk_error(self):
        from unittest.mock import patch
        with patch.object(self.settings.framing, "confirm", lambda restoring=False: restoring):
            widgets, form = self.build()
            # build() leaves the actual framing confirmation untouched.
            widgets["framing:zoom:preset:2"].SetIsChecked(True)
            form.poll()
            self.assertFalse(form.flush(widgets))
            message = widgets["notice"].calls["SetText"][0]
            self.assertIn("camera", message.lower())
            self.assertNotIn("save settings", message.lower())
            self.assertNotIn("try again", message.lower())
            self.assertTrue(form.model.change_language("FR"))
            form.refresh_labels(widgets)
            message = widgets["notice"].calls["SetText"][0]
            self.assertIn("caméra", message.lower())
            self.assertNotIn("sauvegarde", message.lower())

    def test_missing_live_renderer_discloses_an_unavailable_preview(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        runtime = SimpleNamespace(third_person=SimpleNamespace(_bridge_started=True, framing=None))
        with patch.object(self.package.camera, "_runtime", runtime), patch.object(self.package.camera, "_registered", True):
            self.assertEqual(self.package.camera.framing_status(), "unavailable")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
