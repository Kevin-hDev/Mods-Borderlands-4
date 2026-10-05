"""A new aim retries only with freshly validated owners after an identity refusal."""
import unittest
from types import SimpleNamespace as NS

from ads_sdk_test_fixtures import Native, player
from apex_camera_runtime.ads_context import ContextReader
from apex_camera_runtime.ads_session import AdsSession
from apex_camera_runtime.generated_ads import ERROR_CONTEXT, ERROR_IDENTITY


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.pc, self.actor, self.manager, self.animation, self.weapon, collector = player()
        self.actor.ZoomState = NS(bWantsToZoom=True)
        self.native, self.logs, self.live = Native(), [], True
        reader = ContextReader(lambda item: lambda: item if self.live else None,
                               self.native.identify, lambda _: [collector])
        self.session = AdsSession(self.native, reader, self.logs.append)
        self.settings = NS(third_person_ads=lambda: True)

    def prepare(self):
        return self.session.prepare(self.pc, self.actor, self.manager, self.settings,
                                    foot_mode="ThirdPerson", vehicle=False, pending=False)

    def invalidate(self, error):
        self.assertTrue(self.prepare())
        self.assertTrue(self.session.confirm("ThirdPerson"))
        self.native.status.active, self.native.status.error = 0, error
        self.assertFalse(self.prepare())
        self.native.status.error = 0

    def test_held_press_stays_blocked_but_release_reaim_can_retry_the_same_weapon(self):
        for error in (ERROR_IDENTITY, ERROR_CONTEXT):
            with self.subTest(error=error):
                self.setUp()
                self.invalidate(error)
                for _ in range(4):
                    self.assertFalse(self.prepare())
                    self.assertFalse(self.session.confirm("ThirdPerson"))
                self.assertEqual(len(self.native.contexts), 1)
                self.actor.ZoomState.bWantsToZoom = False
                self.assertFalse(self.prepare())
                self.actor.ZoomState.bWantsToZoom = True
                self.assertTrue(self.prepare())
                self.assertTrue(self.session.confirm("ThirdPerson"))
                self.assertEqual([context.generation for context in self.native.contexts], [1, 2])

    def test_reaim_with_expired_weak_owners_never_publishes_again(self):
        self.invalidate(ERROR_IDENTITY)
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.live = False
        self.actor.ZoomState.bWantsToZoom = True
        self.assertFalse(self.prepare())
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(len(self.native.contexts), 1)

    def test_identity_abandonment_keeps_the_refusal_visible_in_the_same_frame(self):
        from apex_camera_runtime.ads_status import notice
        self.invalidate(ERROR_IDENTITY)
        self.manager.GetActorCameraMode = lambda _actor: "Default"
        controller = NS(ads=self.session, _lifetime=NS(owned=lambda: (self.actor, self.manager)))
        self.assertEqual(self.session.feedback.reason, "reference_unavailable")
        self.assertEqual(notice(controller), "mode_unavailable")
        # This double clears successfully: the preceding identity refusal is not a cleanup error.
        self.assertFalse(any("ownership abandoned" in message for message in self.logs))

    def test_owner_expiry_between_prepare_and_confirm_refuses_publication(self):
        self.assertTrue(self.prepare())
        self.live = False
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(self.native.contexts, [])

    def test_native_serial_change_between_capture_and_confirm_refuses_publication(self):
        from apex_camera_runtime.generated_ads import ObjectId
        self.assertTrue(self.prepare())
        self.native.identify = lambda item: ObjectId(item._get_address(), item._get_address() // 16, 2)
        self.session.reader.identify = self.native.identify
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(self.native.contexts, [])

    def test_confirmation_status_exception_is_a_safe_refusal_with_one_type_diagnostic(self):
        self.assertTrue(self.prepare())
        def stats():
            raise OSError("C:/private/secret.dll")
        self.native.stats = stats
        try:
            self.assertFalse(self.session.confirm("ThirdPerson"))
        except OSError:
            self.fail("Confirmation must refuse a failing status read without escaping the camera flow")
        self.assertEqual(self.native.contexts, [])
        self.assertEqual(sum("OSError" in message for message in self.logs), 1)
        self.assertFalse(any("private" in message or "secret" in message for message in self.logs))

    def test_cleanup_context_abandonment_is_reported_from_cleanup_result(self):
        for prior, cleanup in ((ERROR_IDENTITY, 0), (0, ERROR_CONTEXT), (0, ERROR_IDENTITY)):
            with self.subTest(prior=prior, cleanup=cleanup):
                self.setUp()
                self.prepare()
                self.session.confirm("ThirdPerson")
                self.native.status.error = prior
                def clear(_generation):
                    self.native.status.error = cleanup
                    return True
                self.native.clear = clear
                self.assertTrue(self.session.stop())
                self.assertEqual(any("ownership abandoned" in line for line in self.logs), bool(cleanup))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
