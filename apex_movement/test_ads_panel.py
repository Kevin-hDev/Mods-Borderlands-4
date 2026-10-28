"""The real window preserves its aiming choice and existing restore semantics."""

import unittest

import movement_ui_fixture as sdk_fixture

sdk_fixture.install()

import apex_movement
from apex_movement import camera_settings, panel_assets, panel_fonts, panel_model, panel_form, panel_view
from apex_movement import panel_preferences
from ads_panel_test_fixtures import AdsPanelTests
from orbit_panel_test_fixtures import OrbitPanelTests


class PanelTests(OrbitPanelTests, AdsPanelTests, unittest.TestCase):
    package = apex_movement
    settings = camera_settings


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
