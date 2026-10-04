"""Bounded reads for the standalone vehicle runtime, derived from the measured cap reader."""

import ctypes
import struct
from ctypes import wintypes
from pathlib import Path

from . import protection_config as cfg


class Memory:
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.GetCurrentProcess.restype = wintypes.HANDLE
        self.process = self.api.GetCurrentProcess()
        self.api.ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID,
                                               ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.api.ReadProcessMemory.restype = wintypes.BOOL
        self.api.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        self.api.GetModuleHandleW.restype = wintypes.HMODULE
        self.api.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
        self.api.GetModuleFileNameW.restype = wintypes.DWORD

    def read(self, address, size):
        if type(address) is not int or not 65536 <= address < cfg.MAX_ADDRESS:
            raise ValueError("Invalid address")
        if type(size) is not int or not 1 <= size <= cfg.MAX_READ or address + size >= cfg.MAX_ADDRESS:
            raise ValueError("Invalid read")
        output = ctypes.create_string_buffer(size)
        count = ctypes.c_size_t()
        if (not self.api.ReadProcessMemory(self.process, address, output, size, ctypes.byref(count))
                or count.value != size):
            raise OSError("Read refused")
        return output.raw

    def identify(self):
        base = self.api.GetModuleHandleW(None)
        if not base:
            raise ValueError("Module unavailable")
        path = ctypes.create_unicode_buffer(cfg.MAX_MODULE_PATH)
        count = self.api.GetModuleFileNameW(base, path, len(path))
        if not 1 <= count < len(path) or Path(path.value).name.lower() != cfg.EXE_NAME.lower():
            raise ValueError("Unexpected module")
        dos = self.read(base, 64)
        offset = struct.unpack_from("<I", dos, 0x3C)[0]
        if dos[:2] != b"MZ" or not 64 <= offset <= cfg.MAX_HEADER_OFFSET:
            raise ValueError("Invalid header")
        pe = self.read(base + offset, 128)
        if (pe[:6] != b"PE\0\0\x64\x86" or struct.unpack_from("<H", pe, 24)[0] != 0x20B
                or struct.unpack_from("<I", pe, 80)[0] != cfg.IMAGE_SIZE):
            raise ValueError("Unsupported image")
        return base, path.value

    def name(self, raw):
        if type(raw) is not bytes or len(raw) != 8:
            raise ValueError('Invalid name bytes')
        base, _ = self.identify()
        index, number = struct.unpack('<II', raw)
        if index >> 16 >= cfg.MAX_NAME_BLOCKS:
            raise ValueError('Invalid name index')
        address = base + cfg.NAME_POOL_RVA + 16 + (index >> 16) * 8
        block, = struct.unpack('<Q', self.read(address, 8))
        entry = block + (index & 65535) * 2
        header, = struct.unpack('<H', self.read(entry, 2))
        length = header >> 6
        if not 1 <= length <= cfg.MAX_NAME_LENGTH or header & 1:
            raise ValueError('Unsupported name encoding')
        text = self.read(entry + 2, length).decode('utf8')
        return text + ('_' + str(number - 1) if number else '')
