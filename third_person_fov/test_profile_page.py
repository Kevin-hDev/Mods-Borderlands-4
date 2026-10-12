"""The PROFILES page exercised on this mod's actual generated window."""
import unittest
import sdk_stubs as sdk_fixture
sdk_fixture.install()
import third_person_fov
from third_person_fov import settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from third_person_fov import panel_preferences, panel_profile_window
from profile_page_test_fixtures import ProfilePageTests


class Tests(ProfilePageTests, unittest.TestCase):
    package = third_person_fov
    settings = settings


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
