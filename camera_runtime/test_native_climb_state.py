"""Read native attachment and presentation independently; neither alone marks completion."""
import enum
import types
import unittest

from apex_camera_runtime.native_climb_state import read


class ClimbingType(enum.IntEnum):
    NONE = 0
    GETTING_OFF_AT_TOP = 4


class NativeClimbStateTests(unittest.TestCase):
    def actor(self, current=None, kind=0):
        return types.SimpleNamespace(CharacterMovement=types.SimpleNamespace(
            LadderState=types.SimpleNamespace(CurrentClimbable=current),
            LadderAnimState=types.SimpleNamespace(CurrentType=kind)))

    def test_detached_exit_remains_scripted(self):
        self.assertEqual(read(self.actor(kind=ClimbingType.GETTING_OFF_AT_TOP)), (False, True))

    def test_climb_between_scripted_animations_remains_attached(self):
        self.assertEqual(read(self.actor(current=object())), (True, False))

    def test_completed_native_climb_is_inactive(self):
        self.assertEqual(read(self.actor(kind=ClimbingType.NONE)), (False, False))

    def test_short_bottom_exit_is_scripted_even_when_detached(self):
        self.assertEqual(read(self.actor(kind=2)), (False, True))

    def test_missing_animation_is_unknown_not_completed(self):
        actor = self.actor()
        actor.CharacterMovement.LadderAnimState = None
        self.assertIsNone(read(actor))

    def test_missing_attachment_is_unknown_not_completed(self):
        actor = self.actor()
        actor.CharacterMovement.LadderState = None
        self.assertIsNone(read(actor))

    def test_malformed_animation_is_rejected_not_coerced(self):
        for kind in (True, -1, "0", 0.5):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                read(self.actor(kind=kind))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
