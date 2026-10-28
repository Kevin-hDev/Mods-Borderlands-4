"""An old camera owner must not prevent the movement pack from loading or ticking."""
import unittest
import sdk_stubs

state = sdk_stubs.install()

from camera_protocol_test_fixtures import refuses_legacy


class ProtocolTests(unittest.TestCase):
    def test_mixed_protocol_refuses_only_the_camera(self):
        refuses_legacy(self, "apex_movement", "camera_settings")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
