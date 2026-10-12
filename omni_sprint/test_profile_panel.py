"""The camera profile window exercised on this mod's actual generated window."""
import unittest
import sdk_stubs as sdk_fixture
sdk_fixture.install()
import omni_sprint
from omni_sprint import settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from omni_sprint import panel_preferences
from profile_panel_test_fixtures import ProfilePanelTests


class Tests(ProfilePanelTests, unittest.TestCase):
    package = omni_sprint
    settings = settings


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
