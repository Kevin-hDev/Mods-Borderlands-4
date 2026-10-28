"""Integrate the real ADS policy with mode ownership, collision and transitions."""
import unittest
from types import SimpleNamespace as NS
from ads_sdk_test_fixtures import Kind, Native, obj, player
from camera_test_fixtures import Bridge, Hooks, Settings, Bound, args
from apex_camera_runtime.ads_context import ContextReader
from apex_camera_runtime.ads_session import AdsSession
from apex_camera_runtime.third_person import ThirdPersonController
from apex_camera_runtime.runtime import CameraRuntime


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.pc, self.actor, self.manager, self.animation, self.weapon, collector = player()
        self.actor.ZoomState = NS(bWantsToZoom=False)
        self.manager.mode, self.manager.pushes, self.manager.pops = "Default", 0, 0
        def push(_actor, mode, *_args):
            self.manager.mode = mode
            self.manager.pushes += 1
        def pop(*_args):
            self.manager.mode = "Default"
            self.manager.pops += 1
        self.manager.PushActorCameraMode, self.manager.PopActorCameraMode = push, pop
        self.manager.GetActorCameraMode = lambda _: self.manager.mode
        self.transitions = []
        def transition(mode, *arguments):
            self.manager.mode = mode
            self.transitions.append((mode, arguments))
        self.pc.CameraTransition = self.pc.ClientSetCameraMode = transition
        self.native, self.bridge, self.hooks = Native(), Bridge(), Hooks()
        reader = ContextReader(lambda item: lambda: item, self.native.identify, lambda _: [collector])
        self.ads = AdsSession(self.native, reader, lambda _: None)
        self.controller = ThirdPersonController(self.hooks, self.bridge, "ads-test", ads=self.ads)
        self.settings = Settings()
        self.settings.third_person_ads = lambda: True
        self.frame = 0
        self.tick()

    def tick(self):
        self.frame += 1
        self.controller.sync("test", self.pc, self.settings, self.frame)

    def start_aim(self):
        self.actor.ZoomState.bWantsToZoom = True
        self.tick()
        self.native.status.fov_writes += 1
        self.tick()

    def test_ordinary_aim_keeps_one_layer_and_shoulder_remains_available(self):
        self.start_aim()
        self.assertEqual(self.manager.mode, "ThirdPerson")
        self.assertFalse(self.controller._aiming)
        self.assertEqual((self.manager.pushes, self.manager.pops), (1, 0))
        self.assertTrue(self.ads.effective)
        self.assertTrue(self.controller.toggle_shoulder(self.settings))
        self.assertTrue(self.settings.left)
        self.actor.ZoomState.bWantsToZoom = False
        self.tick()
        self.assertTrue(self.settings.left)
        self.native.status.fov_writes += 1
        self.tick()
        self.assertFalse(self.ads.wanted)

    def test_controller_does_not_suspend_ads_for_final_view_collision(self):
        self.start_aim()
        self.tick()
        self.assertNotIn("collision", self.controller._suspensions)
        self.assertTrue(self.ads.wanted)
        self.assertEqual(self.manager.mode, "ThirdPerson")

    def test_all_three_crouch_slide_transition_paths_follow_the_same_policy(self):
        self.start_aim()
        for path, names in __import__("apex_camera_runtime.transitions", fromlist=["REQUESTS"]).REQUESTS.items():
            argument = args("Slide")
            argument.NewCamMode = "Slide"
            call = Bound()
            callback = self.hooks.items[(path, "PRE", "ads-test")]
            self.assertIs(callback(self.pc, argument, None, call), self.hooks.Block)
            self.assertEqual(call.calls[0][0], "ThirdPerson")
        self.assertEqual(self.controller._mode_pushes, 1)

    def test_repeated_default_requests_do_not_reset_an_already_owned_ads_camera(self):
        self.start_aim()
        for path in self.controller._transitions.paths:
            argument = args("Default")
            argument.NewCamMode = "Default"
            argument.bForceResetMode = True
            call = Bound()
            callback = self.hooks.items[(path, "PRE", "ads-test")]
            self.assertIs(callback(self.pc, argument, None, call), self.hooks.Block)
            self.assertEqual(call.calls, [])

    def test_default_request_still_recovers_an_unowned_mode_during_ads(self):
        self.start_aim()
        self.manager.mode = "Slide"
        path = self.controller._transitions.paths[0]
        call = Bound()
        result = self.hooks.items[(path, "PRE", "ads-test")](self.pc, args("Default"), None, call)
        self.assertIs(result, self.hooks.Block)
        self.assertEqual(call.calls[0][0], "ThirdPerson")

    def test_sniper_then_ordinary_without_releasing_aim_balances_layers(self):
        self.start_aim()
        self.animation.WeaponType = Kind.Sniper
        self.tick()
        self.assertTrue(self.controller._aiming)
        self.assertFalse(self.ads.wanted)
        self.assertEqual(self.manager.mode, "Default")
        self.animation.WeaponType = Kind.Assault
        self.tick(); self.tick()
        self.assertEqual(self.manager.mode, "ThirdPerson")
        self.assertEqual(self.controller._mode_pushes, 1)
        self.assertEqual(self.manager.pushes - self.manager.pops, 1)

    def test_vehicle_entry_invalidates_ads_without_an_extra_layer(self):
        self.start_aim()
        pushes = self.manager.pushes
        self.controller._on_transition("ThirdPersonVehicle", "ThirdPersonVehicle")
        self.assertFalse(self.ads.wanted)
        self.assertEqual(self.manager.pushes, pushes)
        self.assertTrue(self.controller._in_vehicle)

    def test_pending_reticle_restoration_does_not_consume_cleanup_retries(self):
        self.start_aim()
        self.native.status.pending = 1
        self.controller.stop()
        self.assertTrue(self.controller.cleanup_pending)
        self.assertEqual(self.bridge.stops, 0)
        self.assertEqual(self.controller.cleanup_retry.attempts, 0)
        retry = self.controller.cleanup_retry
        for frame in range(1, 12):
            retry.retry(self.controller, retry.next_ns + frame * 100_000_000)
        self.assertEqual(retry.attempts, 0)
        cleanup_hooks = [key for key in self.hooks.items if key[2].endswith(":cleanup")]
        self.assertEqual(len(cleanup_hooks), 1)
        self.native.status.pending = 0
        retry.retry(self.controller, retry.next_ns)
        self.assertFalse(self.controller.cleanup_pending)
        self.assertFalse(retry.waiting)
        self.assertEqual(self.hooks.items, {})

    def test_observed_vehicle_keeps_one_layer_and_returns_to_held_ads(self):
        self.start_aim()
        self.manager.mode = "ThirdPersonVehicle"
        self.tick()
        self.assertFalse(self.ads.wanted)
        self.assertTrue(self.controller._in_vehicle)
        self.assertEqual(self.controller._mode_pushes, 1)
        self.manager.mode = "ThirdPerson"
        self.tick(); self.tick()
        self.assertFalse(self.controller._in_vehicle)
        self.assertTrue(self.ads.wanted)
        self.assertEqual(self.manager.pushes - self.manager.pops, 1)

    def test_actual_weapon_swap_invalidates_then_republishes_without_releasing_aim(self):
        self.start_aim()
        generation = self.native.contexts[-1].generation
        replacement = obj(0x19000)
        self.actor.ActiveWeapons.Slots[0].Weapon = replacement
        self.animation.CurrentWeapon = replacement
        self.tick()
        self.assertIn(generation, self.native.clears)
        self.assertGreater(self.native.contexts[-1].generation, generation)
        self.assertEqual(self.native.contexts[-1].references[3].address, 0x19000)
        self.assertFalse(self.controller._aiming)

    def test_animation_gap_waits_without_restarting_the_camera(self):
        self.start_aim()
        self.actor.Mesh.GetAnimInstance = lambda: None
        for _ in range(5): self.tick()
        self.assertEqual((self.bridge.starts, self.bridge.stops), (1, 0))
        self.assertTrue(self.ads.wanted)
        self.assertEqual(self.manager.mode, "ThirdPerson")
        self.actor.Mesh.GetAnimInstance = lambda: self.animation
        self.tick()
        self.assertEqual(self.manager.pushes - self.manager.pops, 1)

    def test_native_zoom_out_and_rapid_reaim_do_not_rebuild_the_owned_camera(self):
        runtime = CameraRuntime(NS(stop=lambda: None, apply=lambda *_: None), self.controller)
        runtime.register("test", 200, self.settings)
        runtime.tick(self.pc, 1)
        starts = self.bridge.starts
        self.start_aim()
        self.native.status.zoom_scale = 0.5
        self.actor.ZoomState.bWantsToZoom = False
        runtime.tick(self.pc, 2)
        self.native.status.pending = 1
        runtime.tick(self.pc, 3)
        self.assertTrue(self.ads.wanted)
        self.actor.ZoomState.bWantsToZoom = True
        runtime.tick(self.pc, 4)
        self.assertFalse(self.controller._aiming)
        self.native.status.pending = 0
        runtime.tick(self.pc, 5)
        self.assertEqual(self.bridge.starts, starts)
        self.assertEqual(self.bridge.stops, 1)  # Initial runtime ownership election only.
        self.assertEqual(self.manager.pushes - self.manager.pops, 1)
        self.assertEqual(self.manager.mode, "ThirdPerson")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ControllerTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
