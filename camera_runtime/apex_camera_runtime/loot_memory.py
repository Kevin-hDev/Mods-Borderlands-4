"""Bounded process-memory access for the validated five-byte container field."""
import ctypes
from ctypes import wintypes
from .loot_constants import FIELD_SIZE


class ProcessMemory:
    def __init__(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        self.process = kernel.GetCurrentProcess()
        self.read_api = kernel.ReadProcessMemory
        self.write_api = kernel.WriteProcessMemory
        for function in (self.read_api, self.write_api):
            function.argtypes = [
                wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID,
                ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
            ]
            function.restype = wintypes.BOOL

    def read(self, address, size):
        if address <= 0 or size != FIELD_SIZE:
            return None
        output = ctypes.create_string_buffer(size)
        done = ctypes.c_size_t()
        ok = self.read_api(
            self.process, ctypes.c_void_p(address), output, size, ctypes.byref(done))
        return output.raw if ok and done.value == size else None

    def write(self, address, value):
        data = bytes(value)
        if address <= 0 or len(data) != FIELD_SIZE:
            return False
        source = ctypes.create_string_buffer(data)
        done = ctypes.c_size_t()
        ok = self.write_api(
            self.process, ctypes.c_void_p(address), source, len(data), ctypes.byref(done))
        return bool(ok) and done.value == len(data)
