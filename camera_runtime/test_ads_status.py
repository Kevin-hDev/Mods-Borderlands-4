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

    def test_heavy_message_waits_for_native_mode_confirmation(self):
        self.animation.WeaponType = Kind.Heavy
        self.assertFalse(self.prepare())
        self.mode = "ThirdPerson"
        self.assertEqual(self.notice(), "cleanup_pending")
        self.mode = "Default"
        self.assertEqual(self.notice(), "heavy_native")

    def test_unknown_category_and_missing_weapon_are_reported(self):
        self.animation.WeaponType = Kind.Precision
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "unknown_weapon")
        self.animation.CurrentWeapon = None
        self.assertFalse(self.prepare())
        self.assertEqual(self.notice(), "unknown_weapon")

    def test_sniper_and_release_have_no_spurious_error(self):
        self.animation.WeaponType = Kind.Sniper
        self.assertFalse(self.prepare())
        self.assertIsNone(self.notice())
        self.native.supported = False
        self.prepare()
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.assertIsNone(self.notice())

    def test_pending_cleanup_overrides_old_error_and_effective_presentation(self):
        self.assertTrue(self.prepare())
        self.session.confirm("ThirdPerson")
        self.native.status.pending = 1
        self.session.effective = True
        self.assertEqual(self.notice(), "cleanup_pending")

    def test_lost_reference_does_not_claim_restored_first_person(self):
        self.animation.WeaponType = Kind.Heavy
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


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
