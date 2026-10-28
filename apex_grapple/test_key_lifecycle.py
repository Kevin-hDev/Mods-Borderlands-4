"""Registration failures must not leave working callbacks or accumulate old bindings."""

import sys
import unittest

import sdk_stubs

state = sdk_stubs.install()

from apex_grapple import frame, game, keys, settings


class KeyLifecycleTests(unittest.TestCase):
    def setUp(self):
        frame.stop()
        self.player = sdk_stubs.FakeCharacter()
        state["pc"] = sdk_stubs.player(self.player, state["mappings"])
        state["kismet"].hit = (4000.0, "StaticMeshActor")
        settings.show_rope.value = False
        frame.on_frame(self.player.anim, 1_000_000_000)

    def tearDown(self):
        frame.stop()

    def test_failed_disable_keeps_only_failed_registration_and_inerts_callbacks(self):
        bound = keys._binds[0]
        callback = bound.callback
        original = bound.disable
        def unavailable():
            raise RuntimeError("disable failed")
        bound.disable = unavailable
        frame.rope.fire(self.player, 1_000_000_000)
        try:
            frame.stop()
            self.assertFalse(frame.rope.busy)
            self.assertIsNone(game.character())
            self.assertEqual(keys._binds, [bound])
            self.assertIsNone(callback(sdk_stubs.event("IE_Pressed")))
            self.assertFalse(frame.rope.busy)
            self.assertFalse(keys.bind(state["mappings"], frame.rope))
            self.assertEqual(keys._binds, [bound])
        finally:
            bound.disable = original
            keys.unbind()
        self.assertFalse(keys._binds)

    def test_old_callback_stays_inert_after_reenable(self):
        callback = state["keybinds"]["Gamepad_RightThumbstick"]
        frame.stop()
        frame.on_frame(self.player.anim, 3_000_000_000)
        self.assertIsNone(callback(sdk_stubs.event("IE_Pressed")))
        self.assertFalse(frame.rope.busy)

    def test_disable_reentrancy_cannot_fire(self):
        bound = keys._binds[0]
        original = bound.disable
        def reentrant():
            self.assertIsNone(bound.callback(sdk_stubs.event("IE_Pressed")))
            original()
        bound.disable = reentrant
        try:
            frame.stop()
        finally:
            bound.disable = original
        self.assertFalse(frame.rope.busy)

    def test_stop_during_enable_does_not_reactivate_keys(self):
        keys.unbind()
        factory = keys.keybind
        def make(*args, **kwargs):
            bound = factory(*args, **kwargs)
            enable = bound.enable
            def stopping():
                enable()
                frame.stop()
            bound.enable = stopping
            return bound
        keys.keybind = make
        try:
            self.assertFalse(keys.bind(state["mappings"], frame.rope))
        finally:
            keys.keybind = factory
        self.assertFalse(keys.is_bound())
        self.assertFalse(keys._binds)

    def test_enable_failure_rolls_back_partial_registration(self):
        keys.unbind()
        factory = keys.keybind
        def make(*args, **kwargs):
            bound = factory(*args, **kwargs)
            enable = bound.enable
            def failing():
                enable()
                raise RuntimeError("enable failed after registration")
            bound.enable = failing
            return bound
        keys.keybind = make
        try:
            with self.assertRaises(RuntimeError):
                keys.bind(state["mappings"], frame.rope)
        finally:
            keys.keybind = factory
        self.assertFalse(keys.is_bound())
        self.assertFalse(keys._binds)
        self.assertFalse(state["keybinds"])

    def test_failed_remap_cancels_rope_without_working_keys(self):
        bound = keys._binds[0]
        disable = bound.disable
        def unavailable():
            raise RuntimeError("disable failed")
        bound.disable = unavailable
        frame.rope.fire(self.player, 1_000_000_000)
        state["pc"].PlayerInput.EnhancedActionMappings = [sdk_stubs.mapping("Action_Melee", "B")]
        try:
            frame._keep_keys(3_000_000_000)
            self.assertFalse(frame.rope.busy)
        finally:
            bound.disable = disable


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(KeyLifecycleTests))
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    sys.exit(0 if result.wasSuccessful() else 1)
