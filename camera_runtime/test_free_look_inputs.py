"""The player's movement keys read from the game's key list, as the game's own list stood on 2026-09-16 (AZERTY)."""

import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.free_look_inputs import MoveKeys, brakes, move_keys, side


def mapping(action, key, *modifiers):
    return NS(Action=NS(Name=action) if action else None, Key=NS(KeyName=key),
              Modifiers=[NS(Class=NS(Name=name)) for name in modifiers])


GAME_LIST = [
    mapping("Action_Jump_HoldToGlide", "SpaceBar"),
    mapping("Action_Move", "Z", "InputModifierSwizzleAxis"),
    mapping("Action_Move", "Q", "InputModifierNegate"),
    mapping("Action_Move", "S", "InputModifierSwizzleAxis", "InputModifierNegate"),
    mapping("Action_Move", "D"),
    mapping("Action_Move", "Gamepad_Left2D", "OakInputModifier_SouthpawAxisCorrector_OnFoot"),
    mapping(None, "P"),
]
KEYS = MoveKeys(right=("D",), left=("Q",), back=("S",))


class MoveKeysTests(unittest.TestCase):
    def test_the_games_list_gives_right_left_and_back(self):
        self.assertEqual(move_keys(GAME_LIST), KEYS)

    def test_keys_chosen_by_the_player_are_followed(self):
        chosen = [mapping("Action_Move", "Left", "InputModifierNegate"), mapping("Action_Move", "Right")]
        self.assertEqual(move_keys(chosen), MoveKeys(("Right",), ("Left",), ()))

    def test_an_empty_list_reads_no_key(self):
        self.assertEqual(move_keys([]), MoveKeys((), (), ()))


class ReadingTests(unittest.TestCase):
    def test_left_key_and_stick_turn_and_the_back_key_brakes(self):
        held = {"Q": 1.0}
        self.assertEqual(side(lambda key: held.get(key, 0.0), KEYS), -1.0)
        stick = {"Gamepad_LeftX": 0.5}
        self.assertEqual(side(lambda key: stick.get(key, 0.0), KEYS), 0.5)
        self.assertTrue(brakes(lambda key: {"S": 1.0}.get(key, 0.0), KEYS))
        self.assertTrue(brakes(lambda key: {"Gamepad_LeftTriggerAxis": 0.9}.get(key, 0.0), KEYS))
        self.assertFalse(brakes(lambda _key: 0.0, KEYS))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
