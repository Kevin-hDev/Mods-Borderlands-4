"""Menu notices use current diagnostics and never promise an unconfirmed fallback."""

import importlib.util
import unittest
from types import SimpleNamespace as NS

from ads_sdk_test_fixtures import Kind, Native, player
from apex_camera_runtime.ads_context import ContextReader
from apex_camera_runtime.ads_session import AdsSession


class AdsStatusTests(unittest.TestCase):
    def setUp(self):
        self.pc, self.actor, self.manager, self.animation, self.weapon, collector = player()
        self.actor.ZoomState = NS(bWantsToZoom=True)
        self.mode = "Default"
        self.manager.GetActorCameraMode = lambda _actor: self.mode
        self.native, self.logs = Native(), []
        reader = ContextReader(lambda item: lambda: item, self.native.identify, lambda _: [collector])
        self.session = AdsSession(self.native, reader, self.logs.append)
        self.controller = NS(ads=self.session, _lifetime=NS(owned=lambda: (self.actor, self.manager)))
        self.settings = NS(third_person_ads=lambda: True, third_person_enabled=lambda: True)

    def prepare(self):
        return self.session.prepare(self.pc, self.actor, self.manager, self.settings,
                                    foot_mode="ThirdPerson", vehicle=False, pending=False)

    def notice(self):
        self.assertIsNotNone(importlib.util.find_spec("apex_camera_runtime.ads_status"))
        from apex_camera_runtime.ads_status import notice
        return notice(self.controller)

    def test_unsupported_is_current_and_clears_on_a_successful_retry(self):
        self.native.supported = False
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "unsupported")
        for _ in range(3):
            self.prepare()
        self.assertEqual(len(self.logs), 1)
        self.native.supported = True
        self.assertTrue(self.prepare())
        self.assertIsNone(self.notice())

    def test_unknown_weapon_message_waits_for_native_mode_confirmation(self):
        self.animation.WeaponType = Kind.Precision
        self.assertFalse(self.prepare())
        self.mode = "ThirdPerson"
        self.assertEqual(self.notice(), "cleanup_pending")
        self.mode = "Default"
        self.assertEqual(self.notice(), "unknown_weapon")

    def test_unknown_category_and_missing_weapon_are_reported(self):
        self.animation.WeaponType = Kind.Precision
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "unknown_weapon")
        self.animation.CurrentWeapon = None
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "unknown_weapon")

    def test_sniper_has_no_spurious_error(self):
        self.animation.WeaponType = Kind.Sniper
        self.assertFalse(self.prepare())
        self.assertIsNone(self.notice())

    def test_a_heavy_weapon_on_bdl4_is_the_players_choice_not_an_error(self):
        self.animation.WeaponType = Kind.Heavy
        self.assertFalse(self.prepare())
        self.assertIsNone(self.notice())

    def test_terminal_unsupported_remains_visible_after_release_without_spam(self):
        self.native.supported = False
        self.prepare()
        self.actor.ZoomState.bWantsToZoom = False
        for _ in range(10):
            self.assertFalse(self.prepare())
            self.assertEqual(self.notice(), "unsupported")
        self.assertEqual(len(self.logs), 1)

    def test_prepare_exception_is_not_mislabeled_as_an_unsupported_version(self):
        def broken():
            raise OSError("C:/private/secret.dll")
        self.native.prepare = broken
        for _ in range(3):
            self.assertFalse(self.prepare())
            self.assertEqual(self.notice(), "install_failed")
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.assertIsNone(self.notice())
        self.assertEqual(sum("OSError" in message for message in self.logs), 1)
        self.assertFalse(any("private" in message or "secret" in message for message in self.logs))

    def test_bridge_terminal_refusal_is_visible_before_first_press(self):
        self.actor.ZoomState.bWantsToZoom = False
        self.native._prepared, self.native.reason = False, "unavailable"
        self.assertEqual(self.notice(), "unsupported")
        self.native.reason = "preparation_failed"
        self.assertEqual(self.notice(), "install_failed")
        self.assertEqual(self.logs, [])
        self.assertEqual(self.native.contexts, [])

    def test_transient_exception_clears_at_idle_and_next_press_recovers(self):
        original = self.native.prepare
        def broken():
            raise OSError("C:/private/secret.dll")
        self.native.prepare = broken
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "install_failed")
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.assertIsNone(self.notice())
        self.native.prepare = original
        self.actor.ZoomState.bWantsToZoom = True
        self.assertTrue(self.prepare())
        self.assertTrue(self.session.confirm("ThirdPerson"))

    def test_pending_press_observes_terminal_refusal_without_switching_mid_aim(self):
        self.native.supported = None
        self.assertFalse(self.prepare())
        self.native.supported = False
        for _ in range(3):
            self.assertFalse(self.prepare())
            self.assertEqual(self.notice(), "unsupported")
        self.assertEqual(len(self.logs), 1)
        self.assertEqual(self.native.contexts, [])

    def test_pending_cleanup_overrides_old_error_and_effective_presentation(self):
        self.assertTrue(self.prepare())
        self.session.confirm("ThirdPerson")
        self.native.status.pending = 1
        self.session.effective = True
        self.assertEqual(self.notice(), "cleanup_pending")

    def test_lost_reference_does_not_claim_restored_first_person(self):
        self.animation.WeaponType = Kind.Precision
        self.prepare()
        self.controller._lifetime.owned = lambda: (None, None)
        self.assertEqual(self.notice(), "cleanup_pending")

    def test_runtime_status_is_owner_scoped_and_read_only(self):
        from apex_camera_runtime.runtime import CameraRuntime
        runtime = CameraRuntime(NS())
        runtime.register("camera", 200, self.settings)
        runtime.third_person = self.controller
        self.native.supported = False
        self.prepare()
        self.assertEqual(runtime.ads_status("camera"), "unsupported")
        self.assertIsNone(runtime.ads_status("other"))
        self.settings.third_person_ads = lambda: False
        self.assertIsNone(runtime.ads_status("camera"))
        self.assertEqual(self.native.contexts, [])

    def test_pending_cleanup_outlives_both_saved_switches(self):
        from apex_camera_runtime.runtime import CameraRuntime
        runtime = CameraRuntime(NS())
        runtime.register("camera", 200, self.settings)
        runtime.third_person = self.controller
        self.prepare()
        self.session.confirm("ThirdPerson")
        self.native.status.pending = 1
        self.settings.third_person_ads = lambda: False
        self.assertEqual(runtime.ads_status("camera"), "cleanup_pending")
        self.settings.third_person_enabled = lambda: False
        self.assertEqual(runtime.ads_status("camera"), "cleanup_pending")

    def test_orbit_from_first_person_keeps_aim_refusal_visible_to_its_owner(self):
        from apex_camera_runtime.runtime import CameraRuntime
        runtime = CameraRuntime(NS())
        runtime.register('camera', 200, self.settings)
        runtime.third_person = self.controller
        self.native.supported = False
        self.prepare()
        self.settings.third_person_enabled = lambda: False
        self.settings.orbit_enabled = lambda: True
        self.assertEqual(runtime.ads_status('camera'), 'unsupported')
        self.assertIsNone(runtime.ads_status('other'))
        self.settings.orbit_enabled = lambda: False
        self.assertIsNone(runtime.ads_status('camera'))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
