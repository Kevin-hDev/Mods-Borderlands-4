"""Native refusal codes produce one technical cause and a generic, persistent player notice."""
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.ads_bridge import AdsBridge
from apex_camera_runtime.ads_session import AdsSession
from apex_camera_runtime.ads_status import notice
from test_ads_bridge import Function


class CompatibilityDiagnosticTests(unittest.TestCase):
    def bridge(self, verification, installation, logs):
        library = NS(**{name: Function(lambda *_: 0) for name in
                        ("ads_identify", "ads_publish", "ads_clear", "ads_release", "ads_stats")})
        library.ads_verify_files = Function(lambda: verification)
        library.ads_prepare = Function(lambda: installation)
        bridge = AdsBridge(library, logs.append)
        bridge.start_preflight()
        bridge._preflight.future.result(timeout=2)
        return bridge

    def test_known_refusal_codes_name_the_cause_once_and_keep_unsupported_after_release(self):
        cases = ((20, "sdk_compatibility"), (21, "game_compatibility"),
                 (22, "signature_mismatch"), (23, "sdk_export_missing"), (24, "object_table_unavailable"))
        for stage in ("verification", "installation"):
            for code, expected in cases:
                with self.subTest(stage=stage, code=code):
                    logs = []
                    bridge = self.bridge(code if stage == "verification" else 0,
                                         code if stage == "installation" else 0, logs)
                    session = AdsSession(bridge, None, logs.append)
                    controller = NS(ads=session)
                    actor = NS(ZoomState=NS(bWantsToZoom=True))
                    settings = NS(third_person_ads=lambda: True)
                    def prepare():
                        return session.prepare(None, actor, None, settings,
                                               foot_mode="ThirdPerson", vehicle=False, pending=False)
                    for _ in range(3):
                        self.assertFalse(prepare())
                        self.assertEqual(notice(controller), "unsupported")
                    actor.ZoomState.bWantsToZoom = False
                    self.assertFalse(prepare())
                    self.assertEqual(notice(controller), "unsupported")
                    causes = [line for line in logs if f"reason={expected}" in line]
                    self.assertEqual(len(causes), 1)
                    self.assertIn(stage, causes[0])
                    self.assertFalse(any("/" in line or "\\" in line for line in logs))

    def test_unknown_refusal_is_safe_and_does_not_claim_an_sdk_mismatch(self):
        for verification, installation in ((1, 0), (90, 0), (0, 90)):
            with self.subTest(verification=verification, installation=installation):
                logs = []
                bridge = self.bridge(verification, installation, logs)
                for _ in range(3):
                    self.assertIs(bridge.prepare(), False)
                self.assertEqual(sum("reason=native_failure" in line for line in logs), 1)
                self.assertFalse(any("sdk_compatibility" in line for line in logs))
                self.assertEqual(bridge.reason, "preparation_failed")
                self.assertTrue(any(f"native_status={verification or installation}" in line for line in logs))

    def test_malformed_native_status_never_counts_as_success(self):
        for status in (False, "0", None):
            for stage in ("verification", "installation"):
                with self.subTest(status=status, stage=stage):
                    logs = []
                    bridge = self.bridge(status if stage == "verification" else 0,
                                         status if stage == "installation" else 0, logs)
                    self.assertIs(bridge.prepare(), False)
                    self.assertEqual(sum("reason=invalid_status" in line for line in logs), 1)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
