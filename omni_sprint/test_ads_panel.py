"""The real window preserves its aiming choice and existing restore semantics."""

import unittest

import sdk_stubs as sdk_fixture

sdk_fixture.install()

import omni_sprint
from omni_sprint import settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from omni_sprint import panel_preferences
from ads_panel_test_fixtures import AdsPanelTests
from orbit_panel_test_fixtures import OrbitPanelTests


class PanelTests(OrbitPanelTests, AdsPanelTests, unittest.TestCase):
    package = omni_sprint
    settings = settings


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
