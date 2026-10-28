"""Bounded reads and writes of the game's own memory through the system's ReadProcessMemory and WriteProcessMemory, for
what the SDK does not reach: the nodes of the enemies' decision trees (normal/melee_rest.py). An address that is not
mapped makes the call fail and is reported as None or False, where a direct read would crash the game.

Taken from the enemy research's reader (apex_probe/apex_lootable_native_fields.py, ProcessMemory, used in game from
séance 28 on, docs/enemies/mesures/2026-09-29-systemes-ennemis-01/), as It Follows' own copy: a mod depends on no
other. base is where the game's image starts, which the trees' identities are counted from.
"""

import ctypes
from ctypes import wintypes

MAX_BYTES = 256


class ProcessMemory:
    def __init__(self) -> None:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel.GetModuleHandleW.restype = wintypes.HMODULE
        self.process = kernel.GetCurrentProcess()
        self.base = int(kernel.GetModuleHandleW(None) or 0)
        self.read_api, self.write_api = kernel.ReadProcessMemory, kernel.WriteProcessMemory
        for function in (self.read_api, self.write_api):
            function.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID, ctypes.c_size_t,
                                 ctypes.POINTER(ctypes.c_size_t)]
            function.restype = wintypes.BOOL

    def read(self, address: int, size: int) -> bytes | None:
        """size bytes at address, or None when the address is not readable."""
        if not 0 < address < (1 << 64) - size or not 0 < size <= MAX_BYTES:
            return None
        output = ctypes.create_string_buffer(size)
        done = ctypes.c_size_t()
        ok = self.read_api(self.process, ctypes.c_void_p(address), output, size, ctypes.byref(done))
        return output.raw if ok and done.value == size else None

    def write(self, address: int, data: bytes) -> bool:
        """Whether all of data was written at address."""
        if not 0 < address < (1 << 64) - len(data) or not 0 < len(data) <= MAX_BYTES:
            return False
        source = ctypes.create_string_buffer(data, len(data))
        done = ctypes.c_size_t()
        ok = self.write_api(self.process, ctypes.c_void_p(address), source, len(data), ctypes.byref(done))
        return bool(ok) and done.value == len(data)
