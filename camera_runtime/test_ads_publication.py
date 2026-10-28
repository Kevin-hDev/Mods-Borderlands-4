"""The aim context: a generation past ours and the .dll's, never the last one; the owners' key; the contract filled."""
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.ads_publication import LAST_GENERATION, context, next_generation, owner_key
from apex_camera_runtime.generated_ads import ADS_ABI, ObjectId, PathsConfig


class PublicationTests(unittest.TestCase):
    def test_the_generation_passes_both_counters(self):
        self.assertEqual(next_generation(4, 9), 10)
        self.assertEqual(next_generation(12, 9), 13)

    def test_the_last_generation_is_never_handed_out(self):
        self.assertEqual(next_generation(LAST_GENERATION - 2, 0), LAST_GENERATION - 1)
        self.assertIsNone(next_generation(LAST_GENERATION - 1, 0))

    def test_the_key_names_the_owners_and_the_weapon_type(self):
        snapshot = NS(references=(ObjectId(0x10, 1, 2), ObjectId(0x20, 3, 4)), category=4)
        self.assertEqual(owner_key(snapshot), (((0x10, 1, 2), (0x20, 3, 4)), 4))

    def test_the_context_carries_the_generation_owners_and_paths(self):
        references = tuple(ObjectId(0x1000 * (n + 1), n, n + 1) for n in range(8))
        filled = context(NS(references=references, paths=PathsConfig()), 42)
        self.assertEqual((filled.abi, filled.generation, filled.enabled), (ADS_ABI, 42, 1))
        self.assertEqual(filled.references[5].address, 0x6000)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
