"""A Windows message timer on the game thread, independent of paused animations."""

import ctypes
from ctypes import wintypes
import os

PERIOD_MS = 50


class NativeTimer:
    def __init__(self):
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(None, wintypes.HWND, wintypes.UINT,
                                          ctypes.c_size_t, wintypes.DWORD)
        self.api.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, callback_type]
        self.api.SetTimer.restype = ctypes.c_size_t
        self.api.KillTimer.argtypes = [wintypes.HWND, ctypes.c_size_t]
        self.api.KillTimer.restype = wintypes.BOOL
        self.api.GetForegroundWindow.argtypes = []
        self.api.GetForegroundWindow.restype = wintypes.HWND
        self.api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.kernel.GetCurrentThreadId.argtypes = []
        self.kernel.GetCurrentThreadId.restype = wintypes.DWORD
        self.thread = self.kernel.GetCurrentThreadId()
        self.pid = os.getpid()
        self.timer = 0
        self.target = None
        self.error = None
        # The shared clock retains this pointer after KillTimer, including queued messages.
        self.callback = callback_type(self.invoke)

    def check_thread(self):
        if self.kernel.GetCurrentThreadId() != self.thread:
            raise RuntimeError("Menu timer thread changed")

    def available(self):
        self.check_thread()
        window = self.api.GetForegroundWindow()
        pid = wintypes.DWORD()
        thread = self.api.GetWindowThreadProcessId(window, ctypes.byref(pid)) if window else 0
        return bool(thread and pid.value == self.pid)

    def start(self, target):
        self.check_thread()
        if self.timer:
            raise RuntimeError("Menu timer still registered")
        self.target = target
        self.timer = self.api.SetTimer(None, 0, PERIOD_MS, self.callback)
        if not self.timer:
            self.target = None
            raise RuntimeError("Menu timer unavailable")

    def stop(self):
        self.check_thread()
        if self.timer and not self.api.KillTimer(None, self.timer):
            raise RuntimeError("Menu timer could not stop")
        self.timer = 0
        self.target = None

    def invoke(self, _window, _message, timer_id, _stamp):
        try:
            if timer_id == self.timer and self.target is not None:
                self.check_thread()
                self.target()
        except BaseException as error:
            # Never propagate Python exceptions across the native callback boundary.
            self.error = type(error).__name__
            self.target = None
