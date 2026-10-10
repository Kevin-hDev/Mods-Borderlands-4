"""One key's look multiplier (look_multiplier.py): the last InputModifierScalar of Action_Look on that key, scaled from
the game's value, a game write taken as the new base, the game's value back at 1.0 and at stop."""

import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime import look_multiplier
from apex_camera_runtime.look_multiplier import LookMultiplier, find


def scalar(values):
    return NS(Class=NS(Name="InputModifierScalar"), Scalar=NS(X=values[0], Y=values[1], Z=values[2]))


def mapping(modifiers, key, action="Action_Look"):
    return NS(Action=NS(Name=action), Key=NS(KeyName=key), Modifiers=modifiers)


def player(*mappings):
    return NS(PlayerInput=NS(EnhancedActionMappings=list(mappings)))


class CountedMappings(list):
    def __init__(self, values=()):
        super().__init__(values)
        self.scans = 0

    def __iter__(self):
        self.scans += 1
        return super().__iter__()


class MultiplierTests(unittest.TestCase):
    def setUp(self):
        self.first, self.last = scalar((0.8, 0.5, 0.0)), scalar((60.0, 60.0, 0.0))
        self.pc = player(mapping([scalar((9.0, 9.0, 9.0))], "Gamepad_Right2D", action="Action_Move"),
                         mapping([NS(Class=NS(Name="GbxInputModifier_Acceleration")), self.first,
                                  NS(Class=NS(Name="InputModifierScaleByDeltaTime")), self.last, None],
                                 "Gamepad_Right2D"))
        self.unit = LookMultiplier("Gamepad_Right2D", lambda item: (lambda: item), id)

    def step(self, wanted_factor, now_ns):
        self.unit.apply(self.unit.locate(self.pc, now_ns), wanted_factor)

    def test_find_takes_the_last_scalar_of_the_look_action_on_that_key(self):
        self.assertIs(find(self.pc, "Gamepad_Right2D"), self.last)
        self.assertIsNone(find(self.pc, "Mouse2D"))
        self.assertIsNone(find(NS(), "Gamepad_Right2D"))
        self.assertIsNone(find(None, "Gamepad_Right2D"))

    def test_the_factor_scales_the_game_value_and_1_gives_it_back(self):
        self.step(2.0, 1)
        self.assertEqual(look_multiplier.read(self.last), (120.0, 120.0, 0.0))
        self.assertEqual(look_multiplier.read(self.first), (0.8, 0.5, 0.0))
        self.step(2.0, 2)
        self.assertEqual(look_multiplier.read(self.last), (120.0, 120.0, 0.0))
        self.step(1.0, 3)
        self.assertEqual(look_multiplier.read(self.last), (60.0, 60.0, 0.0))
        self.assertIsNone(self.unit.written)

    def test_a_game_write_becomes_the_base_and_stop_gives_it_back(self):
        self.step(0.5, 1)
        look_multiplier.write(self.last, (40.0, 40.0, 0.0))
        self.step(0.5, 2)
        self.assertEqual(look_multiplier.read(self.last), (20.0, 20.0, 0.0))
        self.unit.stop()
        self.assertEqual(look_multiplier.read(self.last), (40.0, 40.0, 0.0))
        self.assertIsNone(self.unit.ref)

    def test_missing_mouse_or_gamepad_is_scanned_once_until_deadline(self):
        for key in ("Mouse2D", "Gamepad_Right2D"):
            with self.subTest(key=key):
                mappings = CountedMappings([mapping([], "Unrelated")])
                pc = NS(PlayerInput=NS(EnhancedActionMappings=mappings))
                unit = LookMultiplier(key, lambda item: lambda: item, id)
                for index in range(60):
                    self.assertIsNone(unit.locate(pc, index * 16_000_000))
                self.assertEqual(mappings.scans, 1)
                mappings.append(mapping([self.last], key))
                self.assertIsNone(unit.locate(pc, 999_999_999))
                self.assertIs(unit.locate(pc, 1_000_000_000), self.last)
                self.assertEqual(mappings.scans, 2)

    def test_new_controller_or_player_input_bypasses_missing_deadline(self):
        for replace_controller in (False, True):
            with self.subTest(replace_controller=replace_controller):
                unit = LookMultiplier("Gamepad_Right2D", lambda item: lambda: item, id)
                pc = player()
                self.assertIsNone(unit.locate(pc, 0))
                found = player(mapping([self.last], "Gamepad_Right2D"))
                if replace_controller:
                    # Keep the input object: the controller alone invalidates the failed search.
                    pc.PlayerInput.EnhancedActionMappings = found.PlayerInput.EnhancedActionMappings
                    pc = NS(PlayerInput=pc.PlayerInput)
                else:
                    pc.PlayerInput = found.PlayerInput
                self.assertIs(unit.locate(pc, 1), self.last)

    def test_input_appearing_and_stop_bypass_missing_deadline(self):
        pc = NS(PlayerInput=None)
        self.assertIsNone(self.unit.locate(pc, 0))
        pc.PlayerInput = self.pc.PlayerInput
        self.assertIs(self.unit.locate(pc, 1), self.last)
        self.unit.stop()
        pc.PlayerInput.EnhancedActionMappings.clear()
        self.assertIsNone(self.unit.locate(pc, 2))
        pc.PlayerInput.EnhancedActionMappings.append(mapping([self.last], "Gamepad_Right2D"))
        self.unit.stop()
        self.assertIs(self.unit.locate(pc, 3), self.last)

    def test_live_reference_avoids_scanning_and_expired_reference_is_not_returned(self):
        gone = set()
        unit = LookMultiplier("Gamepad_Right2D", lambda item: lambda: None if id(item) in gone else item, id)
        mappings = CountedMappings([mapping([self.last], "Gamepad_Right2D")])
        pc = NS(PlayerInput=NS(EnhancedActionMappings=mappings))
        self.assertIs(unit.locate(pc, 0), self.last)
        self.assertIs(unit.locate(pc, 1), self.last)
        self.assertEqual(mappings.scans, 1)
        gone.add(id(self.last))
        mappings.clear()
        self.assertIsNone(unit.locate(pc, 2))
        self.assertIsNone(unit.locate(pc, 3))
        self.assertEqual(mappings.scans, 2)

    def test_lookup_failure_propagates_and_does_not_become_a_cached_miss(self):
        class BrokenMappings:
            def __iter__(self):
                raise RuntimeError("input unavailable")
        pc = NS(PlayerInput=NS(EnhancedActionMappings=BrokenMappings()))
        with self.assertRaises(RuntimeError):
            self.unit.locate(pc, 0)
        pc.PlayerInput.EnhancedActionMappings = [mapping([self.last], "Gamepad_Right2D")]
        self.assertIs(self.unit.locate(pc, 1), self.last)

    def test_recycled_owner_address_does_not_keep_a_missing_result(self):
        gone = set()
        old_pc = player()
        new_pc = player(mapping([self.last], "Gamepad_Right2D"))
        addresses = {id(old_pc): 100, id(new_pc): 100,
                     id(old_pc.PlayerInput): 200, id(new_pc.PlayerInput): 200}
        unit = LookMultiplier("Gamepad_Right2D", lambda item: lambda: None if id(item) in gone else item,
                              lambda item: addresses.get(id(item), id(item)))
        self.assertIsNone(unit.locate(old_pc, 0))
        gone.update((id(old_pc), id(old_pc.PlayerInput)))
        self.assertIs(unit.locate(new_pc, 1), self.last)

    def test_new_wrappers_of_live_owner_do_not_repeat_a_missing_search(self):
        mappings = CountedMappings()
        inputs = NS(EnhancedActionMappings=mappings)
        pc = NS(PlayerInput=inputs)
        unit = LookMultiplier("Gamepad_Right2D", lambda item: lambda: item,
                              lambda item: 100 if hasattr(item, "PlayerInput") else 200)
        self.assertIsNone(unit.locate(pc, 0))
        wrapper = NS(PlayerInput=NS(EnhancedActionMappings=mappings))
        self.assertIsNone(unit.locate(wrapper, 1), None)
        self.assertEqual(mappings.scans, 1)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
