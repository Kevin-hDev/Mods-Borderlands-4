"""Validated native boundary for the rendered-camera interaction ray."""
import ctypes

from .native_bridge import load_packaged_library
from .generated_ads import INTERACTION_ABI

ABI_VERSION = INTERACTION_ABI
LIBRARY_NAME = 'apex_camera_interaction_v2.dll'
HASH_NAME = 'apex_camera_interaction_v2.sha256'
MAX_POINTER = 2**64 - 1 - 0x2000


class Config(ctypes.Structure):
    _fields_ = [('abi', ctypes.c_uint32), ('reserved', ctypes.c_uint32)]
    _fields_ += [(name, ctypes.c_uint64) for name in ('controller', 'pawn', 'manager', 'camera_module')]


class Stats(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ('calls', 'matches', 'valid', 'invalid', 'tick_ms')]
    _fields_ += [(name, ctypes.c_double * 3) for name in ('origin', 'rotation', 'anchor')]
    _fields_ += [(name, ctypes.c_uint32) for name in ('active', 'installed', 'last_success', 'reserved')]
    _fields_ += [(name, ctypes.c_uint64) for name in ('writes', 'bypassed', 'rejected_view')]
    _fields_ += [(name, ctypes.c_double * 3) for name in ('output_origin', 'output_rotation')]


def make_config(pc, manager, camera_library):
    pointers = (pc._get_address(), pc.OakCharacter._get_address(),
                manager._get_address(), camera_library._handle)
    for pointer in pointers:
        if type(pointer) is not int or not 0x10000 <= pointer <= MAX_POINTER or pointer % 8:
            raise ValueError('Invalid interaction owner')
    return Config(ABI_VERSION, 0, *pointers)


def load_library(folder, get_data=None, loader=None):
    return load_packaged_library(folder, get_data, loader,
                                 library_name=LIBRARY_NAME, hash_name=HASH_NAME)


class InteractionBridge:
    def __init__(self, library):
        self.library = library
        library.interaction_start.argtypes = [ctypes.POINTER(Config)]
        library.interaction_start.restype = ctypes.c_int
        library.interaction_stop.argtypes, library.interaction_stop.restype = [], ctypes.c_int
        library.interaction_stats.argtypes = [ctypes.POINTER(Stats)]
        library.interaction_stats.restype = ctypes.c_int

    @staticmethod
    def _check(status):
        if status:
            raise RuntimeError('Native interaction operation refused')

    def start(self, config):
        self._check(self.library.interaction_start(ctypes.byref(config)))

    def stop(self):
        self._check(self.library.interaction_stop())

    def stats(self):
        result = Stats()
        self._check(self.library.interaction_stats(ctypes.byref(result)))
        return result
