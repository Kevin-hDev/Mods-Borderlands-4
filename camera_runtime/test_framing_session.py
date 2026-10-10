"""Framing publication changes no camera ownership and never caches body positions."""
import ctypes
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from ads_sdk_test_fixtures import obj
from apex_camera_runtime.generated_ads import FramingContext, ObjectId, VIEW_ABI
try:
    from apex_camera_runtime.framing_session import FramingSession
except ModuleNotFoundError:
    FramingSession = None


class Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FramingSession, "Framing session missing")
        self.pc, self.actor, self.manager, self.root = [obj(0x10000 * i) for i in range(1, 5)]
        self.pc.OakCharacter, self.pc.PlayerCameraManager = self.actor, self.manager
        self.actor.RootComponent = self.actor.CapsuleComponent = self.root
        self.root.Outer, self.root.AttachParent = self.actor, None
        self.manager.GetActorCameraMode = lambda _: "ThirdPerson"
        self.writes, self.logs, self.serial = [], [], 1
        self.context = NS(capture=lambda item: (lambda: item,
                          ObjectId(item._get_address(), 1, self.serial)))
        self.bridge = NS(publish=self.writes.append, status=lambda: 1)
        self.native = NS(prepare=lambda: True)
        self.session = FramingSession(self.bridge, self.native, self.context, self.logs.append)
        self.values = ((15, False), (10, False), (0, False))
        self.settings = NS(framing_values=lambda: self.values)
        self.controller = NS(_bridge_started=True, _in_vehicle=False, _desired_mode="ThirdPerson",
                             _aiming=False, _aim_returning=False, _suspensions=set(),
                             foot_mode=NS(pending=False), cleanup_retry=NS(pending=False))
        self.layout = patch("apex_camera_runtime.framing_session.make_context", self.make)
        self.layout.start()
        self.addCleanup(self.layout.stop)

    def make(self, actor, root, identities, values):
        result = FramingContext()
        result.abi, result.size = VIEW_ABI, ctypes.sizeof(result)
        result.references[:] = identities
        result.values[:] = values
        return result

    def sync(self):
        self.session.sync(self.controller, self.pc, self.actor, self.manager, self.settings)

    def test_publish_once_live_value_and_serial_changes_republish(self):
        self.sync(); self.sync()
        self.assertEqual(len(self.writes), 1)
        # The native framing gets the aim zoom only: the game places the spacing and height with the shoulder.
        self.assertEqual(tuple(self.writes[-1].values), (15, 0, 0))
        self.values = ((25, False), (20, False), (-10, False))
        self.sync()
        self.assertEqual(len(self.writes), 2)
        self.assertEqual(tuple(self.writes[-1].values), (25, 0, 0))
        self.serial = 2
        self.sync()
        self.assertEqual(len(self.writes), 3)

    def test_orbit_vehicle_and_native_aim_clear_the_optional_framing(self):
        self.sync()
        for field, value in (("_in_vehicle", True), ("_aiming", True), ("_aim_returning", True)):
            setattr(self.controller, field, value)
            self.sync()
            self.assertIsNone(self.writes[-1])
            setattr(self.controller, field, False)
            self.sync()
        self.controller._desired_mode = "Orbit"
        self.sync()
        self.assertIsNone(self.writes[-1])

    def test_orbit_borrow_uses_existing_presets_only_while_third_person_is_displayed(self):
        self.controller._desired_mode = 'Orbit'
        self.controller.presentation_mode = lambda: 'ThirdPerson'
        self.sync()
        self.assertEqual(tuple(self.writes[-1].values), (15, 0, 0))
        self.assertEqual(self.controller._desired_mode, 'Orbit')
        self.manager.GetActorCameraMode = lambda _: 'Orbit'
        self.sync()
        self.assertIsNone(self.writes[-1])

    def test_stop_then_same_owner_republishes_and_invalid_settings_clear(self):
        self.sync(); self.session.stop(); self.sync()
        self.assertEqual(len(self.writes), 3)
        self.values = ((51, True), (10, False), (0, False))
        self.sync()
        self.assertIsNone(self.writes[-1])
        self.assertEqual(self.session.reason, "unavailable")

    def test_metadata_failure_preserves_camera_and_logs_once(self):
        self.layout.stop()
        with patch("apex_camera_runtime.framing_session.make_context", side_effect=ValueError("private")):
            self.sync(); self.sync()
        self.assertEqual(len(self.logs), 1)
        self.assertNotIn("private", self.logs[0])
        self.assertEqual(self.session.reason, "unavailable")

    def test_preflight_pending_never_blocks_or_publishes(self):
        self.native.prepare = lambda: None
        self.sync()
        self.assertEqual(self.writes, [])

    def test_confirmation_waits_for_current_values_and_native_frame(self):
        self.assertTrue(callable(getattr(self.session, "confirm", None)))
        self.assertIsNone(self.session.confirm(self.values))
        self.sync()
        self.assertTrue(self.session.confirm(self.values))

        self.values = ((25, False), (10, False), (0, False))
        self.assertIsNone(self.session.confirm(self.values))
        self.bridge.status = lambda: 0
        self.sync()
        self.assertIsNone(self.session.confirm(self.values))
        self.bridge.status = lambda: 4
        self.sync()
        self.assertFalse(self.session.confirm(self.values))
        self.values = ((15, False), (10, False), (0, False))
        self.sync()
        self.bridge.status = lambda: 1
        self.sync()
        self.assertTrue(self.session.confirm(self.values))

    def test_live_adapter_blocks_foreign_writes_but_allows_local_compensation(self):
        from apex_camera_runtime.framing_session import confirm_settings
        self.settings.third_person_enabled = lambda: True
        self.controller.framing = self.session
        client = NS(owner="test")
        runtime = NS(arbiter=NS(active=lambda: client), third_person=self.controller)
        self.assertIsNone(confirm_settings(runtime, "test", self.settings))
        self.sync()
        self.assertTrue(confirm_settings(runtime, "test", self.settings))

        client.owner = "other"
        self.assertFalse(confirm_settings(runtime, "test", self.settings))
        self.assertTrue(confirm_settings(runtime, "test", self.settings, True))
        client.owner = "test"
        self.controller._in_vehicle = True
        self.assertTrue(confirm_settings(runtime, "test", self.settings))

    def test_old_native_refusal_does_not_reject_a_new_zero_zoom_candidate(self):
        self.bridge.status = lambda: 4
        self.sync()
        self.assertFalse(self.session.confirm(self.values))
        self.values = ((0, False), (10, False), (0, False))
        self.assertIsNone(self.session.confirm(self.values))
        self.bridge.status = lambda: 0
        self.sync()
        self.assertEqual(tuple(self.writes[-1].values), (0, 0, 0))
        self.assertIsNone(self.session.confirm(self.values))
        self.bridge.status = lambda: 1
        self.sync()
        self.assertTrue(self.session.confirm(self.values))

    def test_dormant_camera_saves_choices_without_waiting_for_a_rendered_frame(self):
        from apex_camera_runtime.framing_session import confirm_settings
        self.settings.third_person_enabled = lambda: True
        self.controller.framing = self.session
        runtime = NS(arbiter=NS(active=lambda: NS(owner="test")), third_person=None)
        self.assertTrue(confirm_settings(runtime, "test", self.settings))
        runtime.third_person = self.controller
        self.controller._bridge_started = False
        self.assertTrue(confirm_settings(runtime, "test", self.settings))
        self.assertTrue(confirm_settings(runtime, "test", self.settings, True))

    def test_terminal_native_refusal_keeps_dormant_choices_editable(self):
        from apex_camera_runtime.framing_session import confirm_settings
        self.settings.third_person_enabled = lambda: True
        self.controller.framing = self.session
        runtime = NS(arbiter=NS(active=lambda: NS(owner="test")), third_person=self.controller)
        self.native.prepare = lambda: False
        self.sync()
        self.assertTrue(confirm_settings(runtime, "test", self.settings))
        self.assertTrue(confirm_settings(runtime, "test", self.settings, True))
        self.assertEqual(self.writes, [])
        self.native.prepare = lambda: True
        self.bridge.status = lambda: 0
        self.sync()
        self.assertIsNone(confirm_settings(runtime, "test", self.settings))

    def test_optional_renderer_missing_allows_storing_without_preview(self):
        from apex_camera_runtime.framing_session import confirm_settings
        self.settings.third_person_enabled = lambda: True
        self.controller.framing = None
        runtime = NS(arbiter=NS(active=lambda: NS(owner="test")), third_person=self.controller)
        self.assertTrue(confirm_settings(runtime, "test", self.settings))

    def test_position_only_result_does_not_claim_historical_position_or_repeat_per_press(self):
        self.bridge.status = lambda: 4
        for _ in range(5):
            self.sync()
            self.assertEqual(self.session.reason, "zoom_unavailable")
            self.assertFalse(self.session.confirm(self.values))
            self.session.stop()
        self.assertEqual(len(self.logs), 1)
        self.assertNotIn("historical framing retained", self.logs[0])

    def test_position_change_can_confirm_when_only_unchanged_zoom_is_refused(self):
        self.sync()
        self.values = ((15, False), (20, False), (10, False))
        self.bridge.status = lambda: 4
        self.sync()
        self.assertTrue(self.session.confirm(self.values))
        self.values = ((25, False), (20, False), (10, False))
        self.sync()
        self.assertFalse(self.session.confirm(self.values))

    def test_zoom_only_result_confirms_only_previously_rendered_position(self):
        self.sync()
        self.assertTrue(self.session.confirm(self.values))
        self.values = ((25, False), (10, False), (0, False))
        self.bridge.status = lambda: 6
        self.sync()
        self.assertEqual(self.session.reason, "position_unavailable")
        self.assertTrue(self.session.confirm(self.values))
        self.values = ((25, False), (20, False), (0, False))
        self.sync()
        self.assertFalse(self.session.confirm(self.values))


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
