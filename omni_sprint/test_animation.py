"""The backward carrier belongs to one body and is restored on every context change."""

import sys
import types
import unittest

import sdk_stubs

state = sdk_stubs.install()

from omni_sprint import animation  # noqa: E402


def obj(address, **values):
    return types.SimpleNamespace(_get_address=lambda: address, **values)


class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.notes = []
        self.builds = []
        self.sources = []
        self.targets = []

        def make_source(address):
            source = obj(address, Class=types.SimpleNamespace(Name='BlendSpace'))
            self.sources.append(source)
            return source

        self.source = make_source(20)
        self.make_source = make_source
        self.forward = obj(30, _type=types.SimpleNamespace(Name='GbxAnimNode_BlendSpacePlayer'),
                           AnimAssetKey=obj(31, _type=types.SimpleNamespace(Name='GameplayTag'),
                                            TagName='AnimSet.Player.3rd.BS_Sprint'), BlendSpace=self.source)
        self.backward = obj(40, _type=types.SimpleNamespace(Name='GbxAnimNode_BlendSpacePlayer'),
                            AnimAssetKey=obj(41, _type=types.SimpleNamespace(Name='GameplayTag'),
                                             TagName='AnimSet.Player.3rd.Run_B'), BlendSpace=None)
        self.node = obj(50, _type=types.SimpleNamespace(Name='GbxAnimNode_Locomotion'),
                        BlendSpacePlayers=[self.forward, self.backward])
        self.anim = obj(10, Class=types.SimpleNamespace(Name='BPAnim_Player_3rd_C'),
                        GbxAnimGraphNode_Locomotion_2=self.node, bIsSprinting=True, bIsBackward=True)
        self.movement = obj(60, bIsSprinting=True, MovementMode=1)
        self.character = obj(70, CharacterMovement=self.movement,
                             Mesh=types.SimpleNamespace(GetAnimInstance=lambda: self.anim))

        def build(source, owner):
            self.builds.append(source)
            target = obj(100 + len(self.builds), Class=types.SimpleNamespace(Name='BlendSpace'))
            self.targets.append(target)
            return target

        self.runtime = animation.Runtime(lambda value: lambda: value, build, self.notes.append)

    def prepare_hook(self):
        unreal = sys.modules['unrealsdk']
        original_build = animation.animation_assets.build
        unreal.find_object = lambda *args: None
        unreal.construct_object = lambda **kwargs: None
        sys.modules['unrealsdk.unreal'] = types.SimpleNamespace(WeakPointer=lambda value: lambda: value)
        animation.animation_assets.build = lambda source, owner, find, construct: self.runtime.build(source, owner)
        state['pc'] = types.SimpleNamespace(OakCharacter=self.character)
        animation._runtime = None
        return original_build

    def test_apply_and_keep_original_source(self):
        self.runtime.update(self.character, self.anim, 0)
        self.runtime.update(self.character, self.anim, 1)
        self.assertIs(self.backward.BlendSpace, self.targets[0])
        self.assertIs(self.forward.BlendSpace, self.source)
        self.assertEqual(self.builds, [self.source])

    def test_disable_restores_empty_target(self):
        self.runtime.update(self.character, self.anim, 0)
        self.runtime.stop()
        self.assertIsNone(self.backward.BlendSpace)
        self.assertIs(self.forward.BlendSpace, self.source)

    def test_leaving_sprint_restores_normal_backward_walk(self):
        self.runtime.update(self.character, self.anim, 0)
        self.movement.bIsSprinting = False
        self.anim.bIsSprinting = False
        self.runtime.update(self.character, self.anim, 1)
        self.assertIsNone(self.backward.BlendSpace)

    def test_weapon_change_restores_then_rebuilds(self):
        self.runtime.update(self.character, self.anim, 0)
        second = self.make_source(21)
        self.forward.BlendSpace = second
        self.runtime.update(self.character, self.anim, 1)
        self.assertIs(self.backward.BlendSpace, self.targets[-1])
        self.assertEqual(self.builds, [self.source, second])

    def test_other_mod_replacement_is_not_overwritten(self):
        self.runtime.update(self.character, self.anim, 0)
        foreign = obj(999)
        self.backward.BlendSpace = foreign
        self.runtime.update(self.character, self.anim, 1)
        self.runtime.stop()
        self.assertIs(self.backward.BlendSpace, foreign)
        self.assertEqual(self.builds, [self.source])

    def test_foreign_slot_on_old_body_does_not_block_new_body(self):
        self.runtime.update(self.character, self.anim, 0)
        self.backward.BlendSpace = obj(999)
        self.runtime.update(self.character, self.anim, 1)
        new_back = obj(140, _type=self.backward._type,
                       AnimAssetKey=self.backward.AnimAssetKey, BlendSpace=None)
        new_node = obj(150, _type=self.node._type, BlendSpacePlayers=[self.forward, new_back])
        new_anim = obj(110, Class=self.anim.Class, GbxAnimGraphNode_Locomotion_2=new_node,
                       bIsSprinting=True, bIsBackward=True)
        self.runtime.update(self.character, new_anim, 2)
        self.assertIs(new_back.BlendSpace, self.targets[-1])
        self.assertEqual(len(self.builds), 2)

    def test_character_change_clears_previous_body(self):
        self.runtime.update(self.character, self.anim, 0)
        self.runtime.update(None, None, 1)
        self.assertIsNone(self.backward.BlendSpace)

    def test_not_eligible_does_not_build(self):
        self.anim.bIsBackward = False
        self.runtime.update(self.character, self.anim, 0)
        self.assertFalse(self.builds)

    def test_unsupported_layout_fails_closed(self):
        self.backward.AnimAssetKey.TagName = 'unexpected'
        self.runtime.update(self.character, self.anim, 0)
        self.assertFalse(self.builds)
        self.assertIsNone(self.backward.BlendSpace)

    def test_missing_resource_is_retried_after_delay(self):
        def unavailable(source, owner):
            self.builds.append(source)
            raise ValueError('unavailable')
        self.runtime.build = unavailable
        self.runtime.update(self.character, self.anim, 0)
        self.runtime.update(self.character, self.anim, 1)
        self.assertEqual(len(self.builds), 1)
        self.runtime.update(self.character, self.anim, animation.RETRY_NS)
        self.assertEqual(len(self.builds), 2)
        self.assertIsNone(self.backward.BlendSpace)

    def test_game_hook_uses_played_body_and_applies_private_asset(self):
        original_build = self.prepare_hook()
        try:
            animation.tick(self.anim, 0)
            self.assertIs(self.backward.BlendSpace, self.targets[0])
            animation.stop()
            self.assertIsNone(self.backward.BlendSpace)
        finally:
            animation.animation_assets.build = original_build
            animation._runtime = None

    def test_hook_removes_old_carrier_when_player_disappears(self):
        original_build = self.prepare_hook()
        try:
            animation.tick(self.anim, 0)
            self.assertIs(self.backward.BlendSpace, self.targets[0])
            state['pc'] = None
            animation.tick(obj(999, Class=types.SimpleNamespace(Name='OtherAnim')), 1)
            self.assertIsNone(self.backward.BlendSpace)
        finally:
            animation.animation_assets.build = original_build
            animation._runtime = None

    def test_foreign_callback_does_not_clear_current_body_but_new_body_does(self):
        original_build = self.prepare_hook()
        try:
            animation.tick(self.anim, 0)
            foreign = obj(999, Class=types.SimpleNamespace(Name='BPAnim_Player_3rd_C'))
            animation.tick(foreign, 1)
            self.assertIs(self.backward.BlendSpace, self.targets[0])
            new_body = obj(110, Class=self.anim.Class)
            state['pc'] = types.SimpleNamespace(OakCharacter=obj(120, Mesh=types.SimpleNamespace(
                GetAnimInstance=lambda: new_body)))
            animation.tick(foreign, 2)
            self.assertIsNone(self.backward.BlendSpace)
        finally:
            animation.animation_assets.build = original_build
            animation._runtime = None

    def test_failed_removal_keeps_state_for_retry(self):
        class UnreliablePlayer:
            def __init__(self, previous):
                self._type = previous._type
                self.AnimAssetKey = previous.AnimAssetKey
                self._asset = previous.BlendSpace
                self.reject_once = True

            @property
            def BlendSpace(self):
                return self._asset

            @BlendSpace.setter
            def BlendSpace(self, value):
                if value is None and self.reject_once:
                    self.reject_once = False
                    raise RuntimeError('temporary native setter error')
                self._asset = value

        self.backward = UnreliablePlayer(self.backward)
        self.node.BlendSpacePlayers[1] = self.backward
        self.runtime.update(self.character, self.anim, 0)
        animation._runtime = self.runtime
        try:
            with self.assertRaises(RuntimeError):
                animation.stop()
            self.assertIs(animation._runtime, self.runtime)
            self.assertIs(self.backward.BlendSpace, self.targets[0])
            animation.stop()
            self.assertIsNone(self.backward.BlendSpace)
        finally:
            animation._runtime = None


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(AnimationTests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
