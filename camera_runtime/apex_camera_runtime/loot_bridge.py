"""Load the range-only DLL through the shared verified asset loader."""
import ctypes
from .native_bridge import load_packaged_library

ABI_VERSION = 1
LIBRARY_NAME = 'apex_camera_loot_v1.dll'
HASH_NAME = 'apex_camera_loot_v1.sha256'


class LootBridge:
    def __init__(self, folder):
        self.library = load_packaged_library(folder, library_name=LIBRARY_NAME, hash_name=HASH_NAME)
        for name, args in (('loot_start', [ctypes.c_uint32, ctypes.c_float]),
                           ('loot_distance', [ctypes.c_float]), ('loot_stop', [])):
            function = getattr(self.library, name)
            function.argtypes, function.restype = args, ctypes.c_int

    @staticmethod
    def check(status):
        if status:
            raise RuntimeError('Loot range operation refused')

    def start(self, distance):
        self.check(self.library.loot_start(ABI_VERSION, distance))

    def refresh(self, distance):
        self.check(self.library.loot_distance(distance))

    def stop(self):
        self.check(self.library.loot_stop())
