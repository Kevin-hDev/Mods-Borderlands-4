"""Reads and writes the game's own memory, for the one value no SDK field reaches.

Through ReadProcessMemory and WriteProcessMemory on the game's own process rather than a raw pointer: a wrong address
makes the call fail instead of crashing the game (checked on 2026-09-19 with the address 0x10).
"""

import ctypes
import functools
import struct
from ctypes import wintypes
from typing import Any


@functools.cache
def _kernel() -> Any:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    for name in ("ReadProcessMemory", "WriteProcessMemory"):
        function = getattr(kernel, name)
        function.argtypes = [
            wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
        ]
        function.restype = wintypes.BOOL
    return kernel


def read(address: int, size: int) -> bytes | None:
    """The bytes at this address, or None when any of them cannot be read."""
    kernel = _kernel()
    buffer = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    ok = kernel.ReadProcessMemory(kernel.GetCurrentProcess(), ctypes.c_void_p(address), buffer, size, ctypes.byref(got))
    return buffer.raw[: got.value] if ok and got.value == size else None


def write(address: int, data: bytes) -> bool:
    kernel = _kernel()
    done = ctypes.c_size_t()
    ok = kernel.WriteProcessMemory(
        kernel.GetCurrentProcess(), ctypes.c_void_p(address), ctypes.c_char_p(data), len(data), ctypes.byref(done)
    )
    return bool(ok) and done.value == len(data)


def read_float(address: int) -> float | None:
    data = read(address, 4)
    return None if data is None else struct.unpack("<f", data)[0]


def write_float(address: int, value: float) -> bool:
    return write(address, struct.pack("<f", value))
