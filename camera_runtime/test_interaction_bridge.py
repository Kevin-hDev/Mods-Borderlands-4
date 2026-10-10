"""The packaged aim alignment bridge preserves its ABI and validates every owner address."""
import ctypes
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

from apex_camera_runtime import interaction_bridge as bridge


class Function:
    status = 0

    def __call__(self, *args):
        self.last = args
        return self.status


class BoundaryTests(unittest.TestCase):
    def test_config_and_stats_layout(self):
        manager = NS(_get_address=lambda: 0x30000)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        config = bridge.make_config(pc, manager, NS(_handle=0x40000))
        self.assertEqual(ctypes.sizeof(config), 40)
        self.assertEqual(ctypes.sizeof(bridge.Stats), 160)
        self.assertEqual((config.abi, config.reserved), (4, 0))
        for pointer in (0, True, -1, 0x30001, 2**64):
            with self.assertRaises(ValueError):
                bridge.make_config(pc, manager, NS(_handle=pointer))

    def test_native_error_is_not_hidden(self):
        library = NS(interaction_start=Function(), interaction_stop=Function(), interaction_stats=Function())
        api = bridge.InteractionBridge(library)
        api.start(bridge.Config(1, 0, 0x10000, 0x20000, 0x30000, 0x40000))
        self.assertEqual(library.interaction_start.last[0]._obj.pawn, 0x20000)
        self.assertIsInstance(api.stats(), bridge.Stats)
        library.interaction_stop.status = 3
        with self.assertRaisesRegex(RuntimeError, r'refused \(3\)$'):
            api.stop()

    def test_packaged_library_matches_its_hash(self):
        # The loader's own check, on the real asset: a new ABI number without a rebuilt library turns this red.
        assets = Path(bridge.__file__).parent / 'assets'
        payload = (assets / bridge.LIBRARY_NAME).read_bytes()
        expected = (assets / bridge.HASH_NAME).read_bytes().decode('ascii')
        self.assertTrue(payload.startswith(b'MZ'))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), expected)

    def test_loader_uses_same_integrity_check_as_camera(self):
        payload = b'MZ' + bytes(range(64))
        digest = hashlib.sha256(payload).hexdigest().encode('ascii')
        names = []

        def read(name):
            names.append(name)
            return payload if name == bridge.LIBRARY_NAME else digest

        with tempfile.TemporaryDirectory() as folder:
            result = bridge.load_library(Path(folder), read, lambda path: path.read_bytes())
            self.assertEqual(result, payload)
            self.assertEqual(names, [bridge.LIBRARY_NAME, bridge.HASH_NAME])


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
