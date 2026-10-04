"""Policy and publication use the real context reader, with the native API substituted."""
import unittest
from types import SimpleNamespace as NS
from ads_sdk_test_fixtures import Kind, Native, player
from apex_camera_runtime.ads_context import ContextReader
from apex_camera_runtime.ads_session import AdsSession


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.pc, self.actor, self.manager, self.animation, self.weapon, collector = player()
        self.actor.ZoomState = NS(bWantsToZoom=True)
        self.native, self.logs = Native(), []
        self.reader = ContextReader(lambda item: lambda: item, self.native.identify, lambda _: [collector])
        self.session = AdsSession(self.native, self.reader, self.logs.append)
        self.settings = NS(third_person_ads=lambda: True)

    def prepare(self, **changes):
        parameters = dict(foot_mode="ThirdPerson", vehicle=False, pending=False)
        parameters.update(changes)
        return self.session.prepare(self.pc, self.actor, self.manager, self.settings, **parameters)

    def test_confirmation_and_effect_are_distinct_from_request(self):
        self.assertTrue(self.prepare())
        self.assertFalse(self.session.effective)
        self.assertFalse(self.session.confirm("Default"))
        self.assertEqual(self.native.contexts, [])
        self.assertTrue(self.session.confirm("ThirdPerson"))
        self.assertFalse(self.session.effective)
        self.native.status.fov_writes += 1
        self.prepare()
        self.assertTrue(self.session.effective)
        self.session.confirm("ThirdPerson")
        self.assertEqual(len(self.native.contexts), 1)

    def test_precision_heavy_unknown_orbit_vehicle_and_pending_fall_back(self):
        for category in (Kind.Sniper, Kind.Precision, Kind.Heavy, True, 0):
            self.animation.WeaponType = category
            self.assertFalse(self.prepare())
        self.animation.WeaponType = Kind.Assault
        for change in ({"foot_mode": "Orbit"}, {"vehicle": True}, {"pending": True}):
            self.assertFalse(self.prepare(**change))

    def test_release_keeps_the_native_zoom_tail_without_republishing(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes = 1
        self.native.status.zoom_scale = 0.5
        self.actor.ZoomState.bWantsToZoom = False
        self.assertTrue(self.prepare())
        self.assertEqual(self.native.releases, [1])
        self.assertEqual(self.native.clears, [])
        self.session.confirm("ThirdPerson")
        self.native.status.fov_writes += 1
        self.native.status.zoom_scale = 0.8
        self.assertTrue(self.prepare())
        self.assertEqual(len(self.native.contexts), 1)
        self.native.status.fov_writes += 1
        self.native.status.zoom_scale = 1.0
        self.assertFalse(self.prepare())
        self.assertEqual(len(self.native.clears), 1)
        self.assertFalse(self.session.confirm("ThirdPerson"))

    def test_reaim_during_zoom_tail_rearms_only_after_natural_hud_restoration(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes, self.native.status.zoom_scale = 1, 0.5
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.native.status.pending = 1
        self.actor.ZoomState.bWantsToZoom = True
        self.assertTrue(self.prepare())
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(len(self.native.contexts), 1)
        self.native.status.pending = 0
        self.assertTrue(self.prepare())
        self.assertTrue(self.session.confirm("ThirdPerson"))
        self.assertEqual([context.generation for context in self.native.contexts], [1, 2])

    def test_disabling_during_zoom_tail_revokes_immediately(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes, self.native.status.zoom_scale = 1, 0.5
        self.actor.ZoomState.bWantsToZoom = False
        self.prepare()
        self.settings.third_person_ads = lambda: False
        self.assertFalse(self.prepare())
        self.assertEqual(self.native.clears, [1])

    def test_scale_one_from_before_release_does_not_end_a_new_zoom_tail(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes, self.native.status.zoom_scale = 1, 1.0
        self.actor.ZoomState.bWantsToZoom = False
        self.assertTrue(self.prepare())
        self.assertEqual(self.native.clears, [])
        self.native.status.fov_writes, self.native.status.zoom_scale = 2, 0.8
        self.assertTrue(self.prepare())
        self.native.status.fov_writes, self.native.status.zoom_scale = 3, 1.0
        self.assertFalse(self.prepare())

    def test_weapon_swap_on_release_cannot_publish_a_new_hip_fire_context(self):
        from ads_sdk_test_fixtures import obj
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes, self.native.status.zoom_scale = 1, 0.5
        self.actor.ZoomState.bWantsToZoom = False
        replacement = obj(0x19000)
        self.actor.ActiveWeapons.Slots[0].Weapon = replacement
        self.animation.CurrentWeapon = replacement
        self.assertFalse(self.prepare())
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(len(self.native.contexts), 1)
        self.assertEqual(self.native.clears, [1])

    def test_animation_absence_waits_without_dismantling_the_camera(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.actor.Mesh.GetAnimInstance = lambda: None
        self.assertTrue(self.prepare())
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertFalse(self.session.effective)
        self.actor.Mesh.GetAnimInstance = lambda: self.animation
        self.assertTrue(self.prepare())
        self.assertTrue(self.session.confirm("ThirdPerson"))
        self.assertEqual(len(self.native.contexts), 2)

    def test_pending_cleanup_blocks_a_new_generation(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.pending = 1
        self.assertFalse(self.session.stop())
        self.assertTrue(self.session.pending)
        self.assertTrue(self.prepare())
        self.assertFalse(self.session.confirm("ThirdPerson"))
        self.assertEqual(len(self.native.contexts), 1)
        self.native.status.pending = 0
        self.assertTrue(self.session.stop())
        self.prepare(); self.session.confirm("ThirdPerson")
        self.assertGreater(self.native.contexts[-1].generation, self.native.contexts[0].generation)

    def test_missing_native_contract_keeps_first_person_and_logs_once(self):
        self.native.supported = False
        for _ in range(10): self.assertFalse(self.prepare())
        self.assertEqual(len(self.logs), 1)
        self.assertEqual(self.native.contexts, [])

    def test_trial_is_opt_in_without_persisting_settings(self):
        self.settings = NS()
        self.assertFalse(self.prepare())
        self.session.set_trial(True)
        self.assertTrue(self.prepare())
        self.session.set_trial(False)
        self.assertFalse(self.prepare())

    def test_wrong_thread_before_first_publication_is_terminal_and_observable(self):
        self.native.status.wrong_thread = 1
        for _ in range(5):
            self.assertFalse(self.prepare())
        self.assertEqual(self.native.contexts, [])
        self.assertEqual(len(self.logs), 1)

    def test_native_context_invalidated_cannot_keep_claiming_effective_ads(self):
        self.prepare(); self.session.confirm("ThirdPerson")
        self.native.status.fov_writes = 1
        self.native.status.active, self.native.status.error = 0, 6
        self.assertFalse(self.prepare())
        self.assertFalse(self.session.wanted)
        self.assertEqual(len(self.native.contexts), 1)

    def test_publication_refusal_does_not_retry_every_frame_or_change_weapon(self):
        failures = []
        def refuse(context):
            failures.append(context)
            raise RuntimeError("Refused")
        self.native.publish = refuse
        for _ in range(5):
            self.prepare(); self.session.confirm("ThirdPerson")
        self.assertEqual(len(failures), 1)
        self.assertIs(self.actor.ActiveWeapons.Slots[0].Weapon, self.weapon)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SessionTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
