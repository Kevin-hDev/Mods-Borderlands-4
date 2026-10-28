# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Work handed from the service's thread to the game thread, without a hook nor a timer (OPTI.md, rules 1 and 18).

Created on the game thread (game_thread_start.py), it owns an invisible message-only window of that thread. post() puts a task in
a bounded queue and posts one Windows message to the window; the game's message loop, which runs on its thread each
frame, paused or not, hands the message to our window procedure, which runs the waiting tasks there. Nothing runs
while nothing is posted. Verified in game for a posted message at trial 8 of the gate probe (docs/mod-settings/
enquetes/2026-10-25-porte-3-branchement-sdk.md), and by every change of the mod's trials on 26 October 2026."""

import collections
import ctypes
import itertools
import threading
from ctypes import wintypes

WM_APP = 0x8000
HWND_MESSAGE = wintypes.HWND(-3)
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
# One class name per window: a class left registered by an earlier run cannot block a new one.
SERIAL = itertools.count(1)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HICON)]


def windows_api():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
    user32.RegisterClassExW.restype = wintypes.ATOM
    user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
    user32.UnregisterClassW.restype = wintypes.BOOL
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
                                       wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    return user32, kernel32


class GameThread:
    def __init__(self, max_tasks: int, on_error=None):
        self.user32, self.kernel32 = windows_api()
        self.on_error = on_error
        self.thread_id = self.kernel32.GetCurrentThreadId()
        self.max_tasks = max_tasks
        self.lock = threading.Lock()
        self.tasks = collections.deque()
        self.posted = False
        self.closed = False
        self.errors = 0
        self.last_error = None
        self.messages = 0
        # Kept for the life of the module: Windows calls through this pointer until the window is destroyed.
        self.procedure = WNDPROC(self.window_procedure)
        self.instance = self.kernel32.GetModuleHandleW(None)
        self.class_name = f"ModSettingsQueue{next(SERIAL)}_{id(self):x}"
        self.window_class = WNDCLASSEXW(cbSize=ctypes.sizeof(WNDCLASSEXW), lpfnWndProc=self.procedure,
                                        hInstance=self.instance, lpszClassName=self.class_name)
        if not self.user32.RegisterClassExW(ctypes.byref(self.window_class)):
            raise OSError(ctypes.get_last_error(), "RegisterClassExW refused")
        self.window = self.user32.CreateWindowExW(0, self.class_name, self.class_name, 0, 0, 0, 0, 0, HWND_MESSAGE,
                                                  None, self.instance, None)
        if not self.window:
            error = ctypes.get_last_error()
            self.user32.UnregisterClassW(self.class_name, self.instance)
            raise OSError(error, "CreateWindowExW refused")

    def post(self, task) -> bool:
        """Any thread. False when the queue is full or closed: the caller says so, nothing waits."""
        with self.lock:
            if self.closed or len(self.tasks) >= self.max_tasks:
                return False
            self.tasks.append(task)
            if self.posted:
                return True
            self.posted = True
        if self.user32.PostMessageW(self.window, WM_APP + 1, 0, 0):
            return True
        with self.lock:
            self.posted = False
            if self.tasks and self.tasks[-1] is task:
                self.tasks.pop()
        return False

    def window_procedure(self, window, message, wparam, lparam):
        if message != WM_APP + 1:
            return self.user32.DefWindowProcW(window, message, wparam, lparam)
        try:
            self.drain()
        except BaseException as error:
            # Never let a Python error cross back into the game's message loop.
            self.record(error)
        return 0

    def drain(self) -> None:
        with self.lock:
            batch = list(self.tasks)
            self.tasks.clear()
            self.posted = False
            self.messages += 1
        for task in batch:
            try:
                task()
            except BaseException as error:
                self.record(error)

    def record(self, error: BaseException) -> None:
        self.errors += 1
        self.last_error = type(error).__name__
        if self.on_error is not None:
            try:
                self.on_error(self.last_error)
            except Exception:
                # The log itself failed: the error stays counted (errors, last_error), told by STOPPED_GAME_SIDE.
                self.errors += 1

    def close(self) -> None:
        """Game thread only (DestroyWindow belongs to the window's thread). Waiting tasks are dropped."""
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.tasks.clear()
        self.user32.DestroyWindow(self.window)
        self.user32.UnregisterClassW(self.class_name, self.instance)
