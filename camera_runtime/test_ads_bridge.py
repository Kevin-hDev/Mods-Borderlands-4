"""Exercise the actual ctypes boundary without starting the game."""
import ctypes
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.ads_bridge import AdsBridge
from apex_camera_runtime.generated_ads import AdsContext, AdsStats, ObjectId


class Function:
    def __init__(self, call): self.call = call
    def __call__(self, *args): return self.call(*args)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.code = 0
        self.pending = 0
        self.library = NS(ads_verify_files=Function(lambda: 0),
            ads_prepare=Function(lambda: self.calls.append("prepare") or self.code),
            ads_identify=Function(self.identify), ads_publish=Function(self.publish),
            ads_clear=Function(lambda generation: self.calls.append(("clear", generation)) or self.code),
            ads_release=Function(lambda generation: self.calls.append(("release", generation)) or self.code),
            ads_stats=Function(self.stats))
        self.bridge = AdsBridge(self.library)
        self.bridge.start_preflight()
        self.bridge._preflight.future.result(timeout=2)

    def identify(self, address, output):
        self.calls.append(("identify", address))
        output._obj.address, output._obj.index, output._obj.serial = address, 1, 2
        return self.code

    def publish(self, context):
        self.calls.append(("publish", context._obj))
        return self.code

    def stats(self, output):
        output._obj.pending = self.pending
        return self.code

    def test_prepare_is_once_and_identity_has_the_generated_type(self):
        self.assertTrue(self.bridge.prepare())
        self.assertTrue(self.bridge.prepare())
        result = self.bridge.identify(NS(_get_address=lambda: 0x10000))
        self.assertIsInstance(result, ObjectId)
        self.assertEqual(result.serial, 2)
        self.assertEqual(self.calls.count("prepare"), 1)
        self.assertEqual(self.library.ads_publish.argtypes, [ctypes.POINTER(AdsContext)])
        self.assertEqual(self.library.ads_stats.argtypes, [ctypes.POINTER(AdsStats)])

    def test_refusal_never_becomes_a_valid_identity(self):
        self.code = 1
        self.assertFalse(self.bridge.prepare())
        with self.assertRaises(RuntimeError):
            self.bridge.identify(NS(_get_address=lambda: 0x10000))
        self.assertFalse(any(isinstance(item, tuple) and item[0] == "identify" for item in self.calls))

    def test_invalid_pointer_never_reaches_native_code(self):
        self.bridge.prepare()
        for pointer in (0, 1, True, -1, 1 << 64):
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                self.bridge.identify(NS(_get_address=lambda: pointer))
        self.assertEqual(self.calls, ["prepare"])

    def test_cleanup_waits_for_natural_restoration_and_errors_stay_generic(self):
        self.pending = 1
        self.assertFalse(self.bridge.clear(7))
        self.pending = 0
        self.assertTrue(self.bridge.clear(7))
        self.code = 1
        with self.assertRaises(RuntimeError): self.bridge.stats()

    def test_release_is_distinct_from_clear_and_validates_the_generation(self):
        self.bridge.prepare()
        self.bridge.release(7)
        self.assertEqual(self.calls, ["prepare", ("release", 7)])
        for generation in (0, True, -1, 1 << 64):
            with self.assertRaises(ValueError): self.bridge.release(generation)
        self.assertEqual(len(self.calls), 2)
        self.code = 1
        with self.assertRaises(RuntimeError): self.bridge.release(7)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BridgeTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
