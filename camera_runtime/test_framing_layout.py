"""Framing owns live identities and reflected offsets, never a cached body position."""
import ctypes
import unittest
from apex_camera_runtime import generated_ads as contract


class LayoutTests(unittest.TestCase):
    def test_context_carries_four_identities_and_bounded_settings(self):
        context = getattr(contract, "FramingContext", None)
        self.assertIsNotNone(context, "Framing contract missing")
        self.assertEqual(ctypes.sizeof(context), 112)
        self.assertEqual(context.references.offset, 8)
        self.assertEqual(context.actor_size.offset, 72)
        self.assertEqual(context.values.offset, 96)
        self.assertEqual(context.reserved.offset, 108)
        self.assertEqual(len(context().references), 4)
        self.assertEqual(len(context().values), 3)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
