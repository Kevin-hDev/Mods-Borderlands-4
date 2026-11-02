# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The three Windows calls of Logs & Conflicts: where unrealsdk.dll was loaded from, the clipboard,
and opening a folder in the Explorer. The calls go through an api object so the tests can play Windows.

Known trap, coded from the start: on 64-bit Windows a function that returns a handle must be declared to return a
pointer, or ctypes cuts the handle to 32 bits and the game may crash."""

import ctypes
import os
import time
from ctypes import wintypes
from pathlib import Path

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
PATH_CHARS = 32768


class WindowsApi:
    """The real kernel32 and user32 functions, with their types declared."""

    def __init__(self):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.GetModuleHandleW = kernel32.GetModuleHandleW
        self.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        self.GetModuleHandleW.restype = ctypes.c_void_p
        self.GetModuleFileNameW = kernel32.GetModuleFileNameW
        self.GetModuleFileNameW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
        self.GetModuleFileNameW.restype = wintypes.DWORD
        self.GetShortPathNameW = kernel32.GetShortPathNameW
        self.GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        self.GetShortPathNameW.restype = wintypes.DWORD
        self.GlobalAlloc = kernel32.GlobalAlloc
        self.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self.GlobalAlloc.restype = ctypes.c_void_p
        self.GlobalLock = kernel32.GlobalLock
        self.GlobalLock.argtypes = [ctypes.c_void_p]
        self.GlobalLock.restype = ctypes.c_void_p
        self.GlobalUnlock = kernel32.GlobalUnlock
        self.GlobalUnlock.argtypes = [ctypes.c_void_p]
        self.GlobalUnlock.restype = wintypes.BOOL
        self.GlobalFree = kernel32.GlobalFree
        self.GlobalFree.argtypes = [ctypes.c_void_p]
        self.GlobalFree.restype = ctypes.c_void_p
        self.OpenClipboard = user32.OpenClipboard
        self.OpenClipboard.argtypes = [ctypes.c_void_p]
        self.OpenClipboard.restype = wintypes.BOOL
        self.EmptyClipboard = user32.EmptyClipboard
        self.EmptyClipboard.restype = wintypes.BOOL
        self.SetClipboardData = user32.SetClipboardData
        self.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
        self.SetClipboardData.restype = ctypes.c_void_p
        self.CloseClipboard = user32.CloseClipboard
        self.CloseClipboard.restype = wintypes.BOOL
        self.memmove = ctypes.memmove

    def module_path(self, handle) -> str:
        buffer = ctypes.create_unicode_buffer(PATH_CHARS)
        length = self.GetModuleFileNameW(handle, buffer, PATH_CHARS)
        return buffer.value if 0 < length < PATH_CHARS else ""

    def short_path(self, path: str) -> str:
        buffer = ctypes.create_unicode_buffer(PATH_CHARS)
        length = self.GetShortPathNameW(path, buffer, PATH_CHARS)
        return buffer.value if 0 < length < PATH_CHARS else ""

    @staticmethod
    def last_error() -> int:
        return ctypes.get_last_error()


def dll_folder(api, dll_name: str):
    """The folder the loaded DLL came from, or None when it is not loaded in this process."""
    handle = api.GetModuleHandleW(dll_name)
    if not handle:
        return None
    path = api.module_path(handle)
    return Path(path).parent if path else None


def homes(api, home: str) -> list:
    """The player's home folder, and its short 8.3 form when Windows gives one: a long user name then reads
    C:\\Users\\KEVINH~1 in some paths, its first letters in clear (security audit, 1 November 2026)."""
    short = api.short_path(home) if home else ""
    return [home] + ([short] if short and short.lower() != home.lower() else [])


def set_clipboard(api, text: str, retries_ms: list, sleep=time.sleep) -> tuple:
    """(ok, tries, step): step names where it failed ('open', 'alloc', 'lock', 'set') or 'done'. The clipboard may be
    held by another program for a moment: a few tries, each after a longer wait. The memory is freed unless Windows
    took it."""
    data = (text + "\0").encode("utf-16-le")
    tries = 0
    for wait_ms in [0] + list(retries_ms):
        if wait_ms:
            sleep(wait_ms / 1000)
        tries += 1
        if api.OpenClipboard(None):
            break
    else:
        return False, tries, "open"
    try:
        api.EmptyClipboard()
        memory = api.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not memory:
            return False, tries, "alloc"
        pointer = api.GlobalLock(memory)
        if not pointer:
            api.GlobalFree(memory)
            return False, tries, "lock"
        api.memmove(pointer, data, len(data))
        api.GlobalUnlock(memory)
        if not api.SetClipboardData(CF_UNICODETEXT, memory):
            api.GlobalFree(memory)
            return False, tries, "set"
        return True, tries, "done"
    finally:
        api.CloseClipboard()


def open_folder(folder, starter=None) -> str:
    """'opened', 'missing' (not a folder) or 'failed_<Windows error number>'. Only the folder the service found
    itself is ever passed here (conception, section 6)."""
    if folder is None or not Path(folder).is_dir():
        return "missing"
    try:
        (starter or os.startfile)(str(folder))
    except OSError as error:
        return f"failed_{getattr(error, 'winerror', None) or error.errno}"
    return "opened"
