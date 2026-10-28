"""Shared menu defaults and invalid saved values."""
import sys
import types
import unittest


class Option:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value = identifier, value


sys.modules['mods_base'] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)
from apex_camera_runtime.loot_options import LootOptions


class OptionsTests(unittest.TestCase):
    def test_defaults_and_switch(self):
        options = LootOptions()
        self.assertEqual(options.distance(), 660)
        options.enabled.value = False
        self.assertEqual(options.distance(), 0)

    def test_bounds(self):
        options = LootOptions()
        for value in (True, '2', float('nan'), float('inf'), 0, 4):
            options.multiplier.value = value
            self.assertEqual(options.distance(), 0)
        options.multiplier.value = 1
        self.assertEqual(options.distance(), 330)
        options.multiplier.value = 3
        self.assertEqual(options.distance(), 990)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
