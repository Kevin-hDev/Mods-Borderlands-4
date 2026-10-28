"""Exercise the writer on a private test page only, never on game memory."""
import ctypes
from ctypes import wintypes as w
from types import SimpleNamespace as NS
import sys
import unittest

from vehicle_unlocks.protection_write import Writer, Region


class Tests(unittest.TestCase):
    def setUp(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.VirtualAlloc.argtypes = [w.LPVOID, ctypes.c_size_t, w.DWORD, w.DWORD]
        self.api.VirtualAlloc.restype = w.LPVOID
        self.api.VirtualFree.argtypes = [w.LPVOID, ctypes.c_size_t, w.DWORD]
        self.api.VirtualFree.restype = w.BOOL
        self.api.VirtualProtect.argtypes = [w.LPVOID, ctypes.c_size_t, w.DWORD, ctypes.POINTER(w.DWORD)]
        self.api.VirtualProtect.restype = w.BOOL
        self.address = self.api.VirtualAlloc(None, 4096, 0x3000, 0x04)
        self.assertTrue(self.address)
        self.memory = NS(read=ctypes.string_at)

    def tearDown(self):
        self.assertTrue(self.api.VirtualFree(self.address, 0, 0x8000))

    def test_actual_write_readback_and_restore_on_test_allocation(self):
        self.assertEqual(ctypes.sizeof(Region), 48)
        writer = Writer(self.memory, self.address)
        writer(self.address, bytes(24), b'A' * 24)
        self.assertEqual(ctypes.string_at(self.address, 32), b'A' * 24 + bytes(8))
        writer(self.address, b'A' * 24, bytes(24))
        self.assertEqual(ctypes.string_at(self.address, 32), bytes(32))

    def test_other_address_length_and_stale_value_refused(self):
        writer = Writer(self.memory, self.address)
        for address, expected, value in ((self.address + 8, bytes(24), b'A' * 24),
                                         (self.address, bytes(23), b'A' * 24),
                                         (self.address, b'B' * 24, b'A' * 24)):
            with self.assertRaises(ValueError):
                writer(address, expected, value)
        self.assertEqual(ctypes.string_at(self.address, 32), bytes(32))

    def test_readonly_and_executable_pages_refused_without_protection_changes(self):
        for protection in (0x02, 0x40):
            previous = w.DWORD()
            self.assertTrue(self.api.VirtualProtect(self.address, 4096, protection, ctypes.byref(previous)))
            with self.assertRaises(ValueError):
                Writer(self.memory, self.address)(self.address, bytes(24), b'A' * 24)
            self.assertEqual(ctypes.string_at(self.address, 24), bytes(24))
            actual = w.DWORD()
            self.assertTrue(self.api.VirtualProtect(self.address, 4096, 0x04, ctypes.byref(actual)))
            self.assertEqual(actual.value, protection)

    def test_spanning_region_boundary_refused(self):
        address = self.address + 4096 - 16
        with self.assertRaises(ValueError):
            Writer(self.memory, address)(address, bytes(24), b'A' * 24)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
