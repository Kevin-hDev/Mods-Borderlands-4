"""Real settings and adapter share one persistent aiming choice."""

import unittest

import sdk_stubs

sdk_stubs.install()

from apex_movement import camera, mod, camera_settings
from ads_menu_test_fixtures import AdsSettingsTests


class SettingsTests(AdsSettingsTests, unittest.TestCase):
    settings = camera_settings
    adapter = camera.ADAPTER
    mod = mod


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
