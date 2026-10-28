"""Reloading a game must never reuse animation/effect objects from the previous world."""

import sys
import types
import unittest

import sdk_stubs

state = sdk_stubs.install()
import unrealsdk
from apex_grapple import beam, frame, game, keys

SECOND = 1_000_000_000
NAMES = (game.GRAPPLE_ANIMATION, game.BEAM_EFFECT)


class AssetLifecycleTests(unittest.TestCase):
    def setUp(self):
        frame.stop()
        self.parameters = state["objects"][game.BEAM_EFFECT].ExposedParameters
        self.lookups = []
        self.original_lookup = unrealsdk.find_object
        def find(kind, path):
            self.lookups.append((kind, path))
            return self.original_lookup(kind, path)
        unrealsdk.find_object = find
        self.replace_assets()
        self.new_player()

    def tearDown(self):
        unrealsdk.find_object = self.original_lookup
        frame.stop()
        self.replace_assets()

    def replace_assets(self):
        state["objects"][game.GRAPPLE_ANIMATION] = sdk_stubs.FakeSequence()
        state["objects"][game.BEAM_EFFECT] = types.SimpleNamespace(ExposedParameters=self.parameters)

    def new_player(self):
        self.player = sdk_stubs.FakeCharacter()
        self.hands = sdk_stubs.FakeArms(self.player)
        self.hands.Outer.DoesSocketExist = lambda name: True
        self.hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
        state["anim_instances"] = [self.hands]
        state["pc"] = sdk_stubs.player(self.player, state["mappings"])
        game.refresh(0, at_once=True)

    def cached_assets(self):
        return (game.grapple_animation(), game.beam_effect())

    def test_menu_transition_discards_assets_even_before_their_collection(self):
        old = self.cached_assets()
        state["pc"].OakCharacter = None
        game.refresh(SECOND, at_once=True)
        self.replace_assets()
        self.new_player()
        self.assertIsNot(game.grapple_animation(), old[0])
        self.assertIsNot(game.beam_effect(), old[1])

    def test_both_collected_assets_are_reacquired_without_a_pawn_change(self):
        for asset in self.cached_assets():
            asset.destroyed = True
        self.replace_assets()
        for name, asset in zip(NAMES, self.cached_assets()):
            self.assertIs(asset, state["objects"][name])

    def test_collected_missing_assets_return_none_and_retry_after_loading(self):
        old = self.cached_assets()
        saved = {name: state["objects"].pop(name) for name in NAMES}
        for asset in old:
            asset.destroyed = True
        try:
            self.assertEqual(self.cached_assets(), (None, None))
        finally:
            state["objects"].update(saved)
        self.replace_assets()
        for name, asset in zip(NAMES, self.cached_assets()):
            self.assertIs(asset, state["objects"][name])

    def test_live_assets_remain_cached_across_repeated_reads(self):
        expected = self.cached_assets()
        for _ in range(10):
            game.refresh(1, at_once=True)
            self.assertEqual(self.cached_assets(), expected)
        self.assertEqual(self.lookups, list(NAMES))

    def test_direct_pawn_replacement_discards_old_assets(self):
        old = self.cached_assets()
        self.replace_assets()
        self.new_player()
        self.assertIsNot(game.grapple_animation(), old[0])
        self.assertIsNot(game.beam_effect(), old[1])

    def test_first_key_after_menu_uses_current_assets_without_toggling_mod(self):
        state["kismet"].hit = (2000.0, "StaticMeshActor")
        now = SECOND
        keys.time.perf_counter_ns = lambda: now
        frame.on_frame(self.player.anim, now)
        state["keybinds"]["V"](sdk_stubs.event("IE_Pressed"))
        frame.rope.let_go("test end", now + SECOND)
        old = self.cached_assets()
        state["pc"].OakCharacter = None
        frame.on_frame(self.player.anim, now + 2 * SECOND)
        for asset in old:
            asset.destroyed = True
        self.replace_assets()
        self.new_player()
        now += 4 * SECOND
        frame.on_frame(self.player.anim, now)
        state["keybinds"]["V"](sdk_stubs.event("IE_Pressed"))
        self.assertIs(self.hands.played[0]["Asset"], state["objects"][game.GRAPPLE_ANIMATION])
        self.assertIs(state["niagara"].spawned[-1]["SystemTemplate"], state["objects"][game.BEAM_EFFECT])
        self.assertIsNotNone(beam._component)


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(AssetLifecycleTests))
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    sys.exit(not result.wasSuccessful())
