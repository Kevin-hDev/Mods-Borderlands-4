# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of windows.py with a fake Windows, plus the real API's types. python test_windows.py

The real clipboard is not touched (it is the player's); the real module lookup is tried on a DLL every process has."""

import ctypes
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import windows as w

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class FakeApi:
    def __init__(self, open_after=1, alloc=0x10, lock=0x20, set_ok=True, path=r"W:\Game\Plugins\unrealsdk.dll"):
        self.open_after, self.alloc, self.lock, self.set_ok, self.path = open_after, alloc, lock, set_ok, path
        self.opens = self.closes = 0
        self.freed = []
        self.written = None

    def OpenClipboard(self, _owner):
        self.opens += 1
        return self.opens >= self.open_after

    def EmptyClipboard(self):
        return True

    def GlobalAlloc(self, _flags, size):
        self.size = size
        return self.alloc

    def GlobalLock(self, _memory):
        return self.lock

    def memmove(self, _pointer, data, size):
        self.written = data[:size]

    def GlobalUnlock(self, _memory):
        return True

    def SetClipboardData(self, kind, memory):
        self.kind = kind
        return memory if self.set_ok else 0

    def GlobalFree(self, memory):
        self.freed.append(memory)

    def CloseClipboard(self):
        self.closes += 1

    def GetModuleHandleW(self, name):
        return 0x1234 if name == "unrealsdk.dll" else 0

    def module_path(self, _handle):
        return self.path


def test_clipboard():
    waits = []
    api = FakeApi()
    expect(w.set_clipboard(api, "héllo", [20, 40, 80], waits.append) == (True, 1, "done"), "copy at first try")
    expect(api.written == "héllo\0".encode("utf-16-le") and api.kind == w.CF_UNICODETEXT, "UTF-16 text with its end")
    expect(api.freed == [] and api.closes == 1, "memory kept by Windows, clipboard closed")
    api = FakeApi(open_after=3)
    expect(w.set_clipboard(api, "x", [20, 40, 80], waits.append) == (True, 3, "done"), "busy clipboard: third try")
    expect(waits == [0.02, 0.04], "growing waits between tries")
    api = FakeApi(open_after=99)
    expect(w.set_clipboard(api, "x", [20, 40, 80], lambda _s: None) == (False, 4, "open"), "gives up after 4 tries")
    expect(api.closes == 0, "nothing to close when never opened")
    api = FakeApi(set_ok=False)
    expect(w.set_clipboard(api, "x", [], lambda _s: None) == (False, 1, "set"), "refused data reported")
    expect(api.freed == [0x10] and api.closes == 1, "refused data: memory freed, clipboard closed")
    api = FakeApi(lock=0)
    expect(w.set_clipboard(api, "x", [], lambda _s: None) == (False, 1, "lock") and api.freed == [0x10],
           "lock failure frees the memory")
    api = FakeApi(alloc=0)
    expect(w.set_clipboard(api, "x", [], lambda _s: None) == (False, 1, "alloc") and api.closes == 1,
           "allocation failure closes the clipboard")


def test_folders():
    expect(w.dll_folder(FakeApi(), "unrealsdk.dll") == Path(r"W:\Game\Plugins"), "DLL folder from its path")
    expect(w.dll_folder(FakeApi(), "other.dll") is None, "DLL not loaded: no folder")
    expect(w.dll_folder(FakeApi(path=""), "unrealsdk.dll") is None, "no path: no folder")
    opened = []
    with tempfile.TemporaryDirectory() as folder:
        expect(w.open_folder(folder, opened.append) == "opened" and opened == [folder], "existing folder opened")

        def refuse(_path):
            raise OSError(5, "denied")

        expect(w.open_folder(folder, refuse) == "failed_5", "refusal reported with its number")
    expect(w.open_folder(None, opened.append) == "missing", "no folder found: nothing opened")
    expect(w.open_folder(r"Z:\no\such\folder", opened.append) == "missing", "missing folder: nothing opened")


def test_homes():
    class ShortApi:
        def __init__(self, short):
            self.short = short

        def short_path(self, _path):
            return self.short

    expect(w.homes(ShortApi("C:\\Users\\JANEDO~1"), "C:\\Users\\Jane Doe")
           == ["C:\\Users\\Jane Doe", "C:\\Users\\JANEDO~1"], "the short name beside the home")
    expect(w.homes(ShortApi("c:\\users\\kevin"), "C:\\Users\\Kevin") == ["C:\\Users\\Kevin"],
           "a short name equal to the home is not repeated")
    expect(w.homes(ShortApi(""), "C:\\Users\\Kevin") == ["C:\\Users\\Kevin"], "no short name: the home alone")


def test_real_api():
    api = w.WindowsApi()
    for name in ("GetModuleHandleW", "GlobalAlloc", "GlobalLock", "GlobalFree", "SetClipboardData"):
        expect(getattr(api, name).restype is ctypes.c_void_p, f"{name} returns a full pointer (64-bit handles)")
    expect(api.GetShortPathNameW.restype is not None and api.short_path(str(Path.home())) != "",
           "the real short path call answers")
    folder = w.dll_folder(api, "kernel32.dll")
    expect(folder is not None and (folder / "kernel32.dll").is_file(), "real lookup finds kernel32's folder")


for test in (test_clipboard, test_folders, test_homes, test_real_api):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
