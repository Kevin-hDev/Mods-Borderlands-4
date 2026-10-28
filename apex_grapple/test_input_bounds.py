"""External input lists and key names must be bounded and rejected as a whole."""

import sys
import unittest

import sdk_stubs

state = sdk_stubs.install()

from apex_grapple import frame, game, input_list, keys


class InputBoundsTests(unittest.TestCase):
    def tearDown(self):
        keys.unbind()

    def test_oversized_mapping_list_is_rejected_without_partial_binding(self):
        mappings = [sdk_stubs.mapping("Action_Melee", "V")] * 1025
        with self.assertRaises(ValueError):
            keys.bind(mappings, frame.rope)
        self.assertFalse(keys._binds)

    def test_oversized_generator_is_not_silently_truncated(self):
        mappings = (sdk_stubs.mapping("Action_Melee", "V") for _ in range(1025))
        state["pc"] = sdk_stubs.player(sdk_stubs.FakeCharacter(), mappings)
        with self.assertRaises(ValueError):
            game.input_mappings()

    def test_invalid_key_and_action_names_are_rejected(self):
        for action, key in (("Action_Melee", "V\nsecret"), ("Action_Melee", "X" * 257),
                            ("Action_Melee\nsecret", "V")):
            with self.subTest(action=action, key=key):
                with self.assertRaises(ValueError):
                    input_list.grapple_keys([sdk_stubs.mapping(action, key)])


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(InputBoundsTests))
    print("RESULTAT:", "TOUS LES TESTS PASSENT" if result.wasSuccessful() else "ECHEC")
    sys.exit(0 if result.wasSuccessful() else 1)
