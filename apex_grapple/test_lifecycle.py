"""Regressions for transient player references and fail-closed frame processing."""

import sys
import unittest

import sdk_stubs

state = sdk_stubs.install()

from apex_grapple import frame, game, keys, settings
from unrealsdk.hooks import Block

SECOND = 1_000_000_000


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        frame.stop()
        self.player = sdk_stubs.FakeCharacter()
        state["pc"] = sdk_stubs.player(self.player, state["mappings"])
        state["kismet"].hit = (4000.0, "StaticMeshActor")
        settings.show_rope.value = False

    def tearDown(self):
        frame.stop()

    def attach(self):
        frame.on_frame(self.player.anim, SECOND)
        frame.rope.fire(self.player, SECOND)
        frame.on_frame(self.player.anim, 2 * SECOND)
        self.assertTrue(frame.rope.holds)

    def press(self, key):
        return state["keybinds"][key](sdk_stubs.event("IE_Pressed"))

    def test_missing_animation_recovers_on_same_character(self):
        animation = self.player.anim
        self.player.anim = None
        frame.on_frame(object(), SECOND)
        self.player.anim = animation
        frame.on_frame(animation, 2 * SECOND)
        self.assertIs(game.anim(), animation)
        self.assertTrue(keys.is_bound())

    def test_animation_lookup_failure_is_retryable(self):
        def unavailable():
            raise RuntimeError("transient animation failure")
        self.player.Mesh.GetAnimInstance = unavailable
        frame.on_frame(object(), SECOND)
        self.player.Mesh.GetAnimInstance = lambda: self.player.anim
        frame.on_frame(self.player.anim, 2 * SECOND)
        self.assertIs(game.anim(), self.player.anim)
        self.assertTrue(keys.is_bound())

    def test_replaced_animation_cancels_old_rope(self):
        self.attach()
        self.player.anim = object()
        frame.on_frame(self.player.anim, 3 * SECOND)
        self.assertIs(game.anim(), self.player.anim)
        self.assertFalse(frame.rope.busy)

    def test_destroyed_character_cancels_before_poll_deadline(self):
        self.attach()
        self.player.destroyed = True
        state["pc"] = None
        frame.on_frame(object(), 2 * SECOND + 1)
        self.assertFalse(frame.rope.busy)
        self.assertIsNone(self.press("SpaceBar"))

    def test_vehicle_press_and_jump_validate_current_possession(self):
        self.attach()
        state["pc"].OakCharacter = None
        self.assertIsNone(self.press("SpaceBar"))
        self.assertFalse(frame.rope.busy)
        self.assertIsNone(self.press("Gamepad_RightThumbstick"))

    def test_vehicle_transition_cancels_on_next_frame_without_a_press(self):
        self.attach()
        before = game.velocity(self.player.CharacterMovement)
        state["pc"].OakCharacter = None
        frame.on_frame(self.player.anim, 2 * SECOND + 16_000_000)
        self.assertEqual(game.velocity(self.player.CharacterMovement), before)
        self.assertFalse(frame.rope.busy)
        self.assertIsNone(game.character())
        self.assertIsNone(self.press("SpaceBar"))
        state["pc"].OakCharacter = self.player
        frame.on_frame(self.player.anim, 2 * SECOND + 32_000_000)
        self.assertIs(self.press("Gamepad_RightThumbstick"), Block)

    def test_new_live_pawn_cancels_old_owner_before_poll_deadline(self):
        self.attach()
        before = game.velocity(self.player.CharacterMovement)
        replacement = sdk_stubs.FakeCharacter()
        state["pc"] = sdk_stubs.player(replacement, state["mappings"])
        frame.on_frame(self.player.anim, 2 * SECOND + 16_000_000)
        self.assertEqual(game.velocity(self.player.CharacterMovement), before)
        self.assertFalse(frame.rope.busy)
        self.assertIs(game.character(), replacement)
        frame.on_frame(replacement.anim, 2 * SECOND + 32_000_000)
        self.assertIs(self.press("Gamepad_RightThumbstick"), Block)

    def test_already_refreshed_context_still_cleans_the_previous_rope(self):
        self.attach()
        replacement = sdk_stubs.FakeCharacter()
        state["pc"] = sdk_stubs.player(replacement, state["mappings"])
        game.refresh(2 * SECOND + 1, at_once=True)
        frame.on_frame(replacement.anim, 2 * SECOND + 16_000_000)
        self.assertFalse(frame.rope.busy)
        self.assertEqual(game.velocity(replacement.CharacterMovement), (0.0, 0.0, 0.0))

    def test_repeated_absent_frames_do_not_repeat_cleanup(self):
        self.attach()
        state["pc"].OakCharacter = None
        original = frame.rope.reset
        calls = []
        def counted():
            calls.append(True)
            original()
        frame.rope.reset = counted
        try:
            for offset in range(1, 5):
                frame.on_frame(object(), (2 * SECOND) + offset * 16_000_000)
        finally:
            frame.rope.reset = original
        self.assertEqual(len(calls), 1)

    def test_refreshing_same_context_elsewhere_does_not_cancel_a_pull(self):
        self.attach()
        before = game.context()
        self.assertFalse(game.refresh(2 * SECOND + 1, at_once=True))
        self.assertIs(game.context(), before)
        frame.on_frame(self.player.anim, 2 * SECOND + 16_000_000)
        self.assertTrue(frame.rope.holds)

    def test_initial_absence_and_return_only_clean_each_context_once(self):
        state["pc"] = None
        original = frame.rope.reset
        calls = []
        def counted():
            calls.append(True)
            original()
        frame.rope.reset = counted
        try:
            for offset in range(4):
                frame.on_frame(object(), SECOND + offset * 16_000_000)
            self.assertEqual(len(calls), 1)
            state["pc"] = sdk_stubs.player(self.player, state["mappings"])
            for offset in range(4):
                frame.on_frame(self.player.anim, 2 * SECOND + offset * 16_000_000)
            self.assertEqual(len(calls), 2)
        finally:
            frame.rope.reset = original
        self.assertIs(self.press("Gamepad_RightThumbstick"), Block)

    def test_forget_cannot_reuse_an_attached_rope_on_the_same_pawn(self):
        self.attach()
        game.forget()
        game.refresh(2 * SECOND + 1, at_once=True)
        frame.on_frame(self.player.anim, 2 * SECOND + 16_000_000)
        self.assertFalse(frame.rope.busy)
        self.assertIs(self.press("Gamepad_RightThumbstick"), Block)

    def test_absent_player_input_stops_rope_and_recovers(self):
        self.attach()
        inputs = state["pc"].PlayerInput
        state["pc"].PlayerInput = None
        frame.on_frame(self.player.anim, 3 * SECOND)
        self.assertFalse(frame.rope.busy)
        state["pc"].PlayerInput = inputs
        frame.on_frame(self.player.anim, 4 * SECOND)
        self.assertIs(self.press("Gamepad_RightThumbstick"), Block)


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(LifecycleTests))
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    sys.exit(0 if result.wasSuccessful() else 1)
