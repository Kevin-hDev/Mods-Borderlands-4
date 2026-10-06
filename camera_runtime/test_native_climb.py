"""Native climbing owns a temporary camera, never a saved choice or extra layer."""
import unittest

from native_climb_test_fixture import NativeClimbFixture


class NativeClimbTests(NativeClimbFixture, unittest.TestCase):
    def test_native_entry_uses_climbing_camera_not_persistent_mode(self):
        self.make()
        self.settings.left = True
        self.enter()
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")
        self.assertEqual(self.controller._desired_mode, "ThirdPerson")
        self.assertEqual((self.manager.pushes, self.manager.pops), (1, 0))
        self.assertTrue(self.settings.left)
        self.assertEqual(self.settings.orbit_saves, 0)

    def test_hold_never_reasserts_or_stacks_per_frame(self):
        self.make()
        self.enter()
        for now in (3, 500_000_000, 4_000_000_000):
            self.frame(now)
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertEqual(self.bridge.stops, 0)

    def test_exit_restores_once_and_waits_before_releasing_shift(self):
        self.make()
        self.enter()
        self.frame(3)
        self.accept = False
        self.ladder.CurrentClimbable = None
        self.frame(4)
        self.frame(5)
        self.assertEqual(self.requests, ["ThirdPersonClimbing", "ThirdPerson"])
        self.assertIn("climb", self.controller._suspensions)
        self.manager.mode = "ThirdPerson"
        self.frame(6)
        self.assertNotIn("climb", self.controller._suspensions)
        self.assertEqual(self.bridge.suspended, [True, False])

    def test_native_exit_already_restored_does_not_request_again(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.manager.mode = "ThirdPerson"
        self.frame(4)
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertNotIn("climb", self.controller._suspensions)

    def test_orbit_and_saved_shoulder_are_restored_without_tp_layer(self):
        self.make(orbit=True)
        self.enter()
        self.ladder.CurrentClimbable = None
        self.frame(4)
        self.frame(5)
        self.assertEqual(self.manager.mode, "Orbit")
        self.assertEqual((self.manager.pushes, self.manager.pops), (0, 0))
        self.assertEqual(self.controller._suspensions, {"orbit"})
        self.assertTrue(self.settings.orbit)
        self.assertEqual(self.settings.orbit_saves, 0)

    def test_aim_input_cannot_override_the_climbing_camera(self):
        self.make()
        self.actor.ZoomState.bWantsToZoom = True
        self.enter()
        self.frame(3)
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")
        self.assertFalse(self.controller._aiming)

    def test_refused_entry_is_bounded_and_rearms_next_climb(self):
        self.make()
        self.accept = False
        self.enter()
        self.frame(900_000_000)
        self.frame(2_000_000_000)
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertEqual(len(self.notes), 2)
        self.assertEqual(self.bridge.stops, 0)
        self.ladder.CurrentClimbable = None
        self.manager.mode = "ThirdPerson"
        self.frame(2_000_000_001)
        self.accept = True
        self.enter(2_000_000_002)
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")

    def test_vehicle_preempts_climb_without_on_foot_restore(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.manager.mode = "ThirdPersonVehicle"
        self.frame(4)
        self.assertEqual(self.manager.mode, "ThirdPersonVehicle")
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertTrue(self.controller._in_vehicle)

    def test_no_climbable_never_rewrites_unrelated_ladder_mode(self):
        self.make()
        self.manager.mode = "ladder"
        self.frame(2)
        self.assertEqual(self.requests, [])

    def test_disable_cleans_up_temporary_mode_and_base_layer(self):
        self.make()
        self.enter()
        self.settings.enabled = False
        self.frame(3)
        self.assertEqual(self.manager.mode, "Default")
        self.assertFalse(self.controller.cleanup_pending)
        self.assertEqual(self.manager.pops, 1)
        self.assertEqual(self.controller._suspensions, set())

    def test_interrupted_orbit_transaction_is_cancelled_not_saved(self):
        self.make()
        self.accept = False
        self.assertTrue(self.controller.set_orbit(self.settings, True, 2))
        self.accept = True
        self.enter(3)
        self.assertFalse(self.controller.foot_mode.pending)
        self.ladder.CurrentClimbable = None
        self.manager.mode = "ThirdPerson"
        self.frame(4)
        self.assertEqual(self.controller.foot_mode.preempted, "")
        self.assertEqual(self.settings.orbit_saves, 0)
        self.assertFalse(self.settings.orbit)

    def test_vehicle_takes_suspension_before_climb_releases_it(self):
        self.make()
        self.enter()
        self.manager.mode = "ThirdPersonVehicle"
        self.frame(3)
        self.assertEqual(self.bridge.suspended, [True])
        self.assertEqual(self.controller._suspensions, {"vehicle"})

    def test_return_refusal_uses_owned_cleanup_without_repeated_requests(self):
        self.make()
        self.enter()
        self.accept = False
        self.ladder.CurrentClimbable = None
        self.frame(4)
        self.frame(900_000_005)
        self.assertEqual(self.requests, ["ThirdPersonClimbing", "ThirdPerson", "Default"])
        self.assertFalse(self.controller.cleanup_pending)
        self.assertEqual(self.manager.pops, 1)

    def test_aiming_before_climb_restores_exactly_one_owned_base_layer(self):
        self.make()
        self.actor.ZoomState.bWantsToZoom = True
        self.frame(2)
        self.assertEqual(self.manager.mode, "Default")
        self.assertEqual(self.controller._mode_pushes, 0)
        self.enter(3)
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")
        self.assertEqual(self.controller._mode_pushes, 1)
        self.assertFalse(self.controller._aiming)

    def test_new_climb_during_return_gets_its_own_camera_request(self):
        self.make()
        self.enter()
        self.accept = False
        self.ladder.CurrentClimbable = None
        self.frame(3)
        self.accept = True
        self.enter(4)
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")

    def test_native_default_request_while_attached_preserves_climbing(self):
        self.make()
        self.enter()
        self.actor.ZoomState.bWantsToZoom = True
        self.assertEqual(self.rewritten_modes(), ["ThirdPersonClimbing"] * 3)

    def test_inputs_wait_for_return_confirmation(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.accept = False
        self.frame(3)
        self.manager.mode = "ThirdPerson"
        self.assertFalse(self.controller.orbit_available())
        self.assertFalse(self.controller.shoulder_available())

    def test_detached_top_exit_keeps_camera_until_animation_finishes(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.animation.CurrentType = 4
        self.frame(4)
        self.frame(820_000_000)
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertIn("climb", self.controller._suspensions)
        self.animation.CurrentType = 0
        self.frame(820_000_001)
        self.frame(820_000_002)
        self.assertEqual(self.requests, ["ThirdPersonClimbing", "ThirdPerson"])
        self.assertNotIn("climb", self.controller._suspensions)

    def test_native_default_during_detached_animation_keeps_climbing(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.animation.CurrentType = 4
        self.assertEqual(self.rewritten_modes(), ["ThirdPersonClimbing"] * 3)

    def test_short_native_animation_without_ladder_camera_is_covered(self):
        self.make(orbit=True)
        self.animation.CurrentType = 2
        self.frame(2)
        self.assertEqual(self.manager.mode, "ThirdPersonClimbing")
        self.animation.CurrentType = 0
        self.frame(3)
        self.frame(4)
        self.assertEqual(self.manager.mode, "Orbit")
        self.assertEqual(self.settings.orbit_saves, 0)

    def test_missing_exit_animation_read_does_not_guess_completion(self):
        self.make()
        self.enter()
        self.ladder.CurrentClimbable = None
        self.actor.CharacterMovement.LadderAnimState = None
        self.frame(4)
        self.assertEqual(self.requests, ["ThirdPersonClimbing"])
        self.assertIn("climb", self.controller._suspensions)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
