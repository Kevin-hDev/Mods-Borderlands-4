"""Write exactly one validated data reference; refuse executable or protected pages."""
import ctypes
from ctypes import wintypes as w
from . import protection_config as cfg


class Region(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', w.DWORD), ('PartitionId', w.WORD),
                ('RegionSize', ctypes.c_size_t), ('State', w.DWORD),
                ('Protect', w.DWORD), ('Type', w.DWORD)]


class Writer:
    def __init__(self, memory, address):
        if (type(address) is not int or not cfg.MIN_ADDRESS <= address < cfg.MAX_ADDRESS
                or address + cfg.LINK_SIZE >= cfg.MAX_ADDRESS or address % 8):
            raise ValueError('Invalid reward reference address')
        self.memory, self.address = memory, address
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetCurrentProcess.restype = w.HANDLE
        self.process = self.api.GetCurrentProcess()
        self.api.VirtualQuery.argtypes = [w.LPCVOID, ctypes.POINTER(Region), ctypes.c_size_t]
        self.api.VirtualQuery.restype = ctypes.c_size_t
        self.api.WriteProcessMemory.argtypes = [w.HANDLE, w.LPVOID, w.LPCVOID, ctypes.c_size_t,
                                                ctypes.POINTER(ctypes.c_size_t)]
        self.api.WriteProcessMemory.restype = w.BOOL

    def __call__(self, address, expected, value):
        if (address != self.address or type(expected) is not bytes or type(value) is not bytes
                or len(expected) != cfg.LINK_SIZE or len(value) != cfg.LINK_SIZE):
            raise ValueError('Reference write exceeds fixed scope')
        info = Region()
        if self.api.VirtualQuery(address, ctypes.byref(info), ctypes.sizeof(info)) != ctypes.sizeof(info):
            raise OSError('Data region unavailable')
        if (info.State != cfg.MEM_COMMIT or info.Protect not in cfg.WRITABLE_DATA
                or not info.BaseAddress or not 0 < info.RegionSize <= cfg.MAX_REGION
                or not info.BaseAddress <= address
                or address + cfg.LINK_SIZE > info.BaseAddress + info.RegionSize):
            raise ValueError('Writable data region required')
        if self.memory.read(address, cfg.LINK_SIZE) != expected:
            raise ValueError('Reward reference changed before write')
        buffer = ctypes.create_string_buffer(value, cfg.LINK_SIZE)
        done = ctypes.c_size_t()
        if (not self.api.WriteProcessMemory(self.process, address, buffer, cfg.LINK_SIZE, ctypes.byref(done))
                or done.value != cfg.LINK_SIZE):
            raise OSError('Reference write incomplete')
        if self.memory.read(address, cfg.LINK_SIZE) != value:
            raise RuntimeError('Reference readback differs')
