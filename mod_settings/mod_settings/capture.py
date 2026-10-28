# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Key capture for the page's keybind row, read through Windows: the game gives a menu page no keys, and the SDK's
keybinds ignore keys while the cursor shows; the HUD Editor proved this reading in game, pause included
(docs/candidats/HUD/investigations/2026-09-28-editeur-complet/releves/2026-10-04-raccourci-integre/README.md).

One capture at a time, on its own thread, which touches no game object. It is the mod's only repeated reading:
bounded to maxSeconds, it stops on the first key, on Escape, on cancel or at the service's stop."""

import ctypes
import os
import threading
import time


class WindowsKeys:
    """The two Windows calls the capture needs; replaced by a stand-in in the tests."""

    def __init__(self):
        from ctypes import wintypes
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.pid_type = wintypes.DWORD
        self.pid = os.getpid()

    def pressed(self, code: int) -> bool:
        return bool(self.user32.GetAsyncKeyState(code) & 0x8000)

    def focused(self) -> bool:
        """Keys count only while the game's window is in front: never a key typed in another program."""
        window = self.user32.GetForegroundWindow()
        if not window:
            return False
        pid = self.pid_type()
        self.user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
        return pid.value == self.pid


class KeyCapture:
    def __init__(self, constants: dict, keys, on_end, clock=time.monotonic):
        capture = constants["capture"]
        self.catalogue = capture["keys"]
        self.cancel_key = capture["cancelKey"]
        self.poll_s = capture["pollMs"] / 1000
        self.max_s = capture["maxSeconds"]
        self.keys = keys
        self.on_end = on_end
        self.clock = clock
        self.lock = threading.Lock()
        self.state = "idle"
        self.key = None
        self.ident = None
        self.stop = threading.Event()
        self.thread = None

    def start(self, ident: str) -> bool:
        with self.lock:
            if self.state == "waiting":
                return False
            self.state, self.key, self.ident = "waiting", None, ident
            self.stop = threading.Event()
            self.thread = threading.Thread(target=self.run, args=(self.stop,), name="mod-settings-capture",
                                           daemon=True)
        self.thread.start()
        return True

    def cancel(self) -> None:
        self.stop.set()

    def status(self) -> tuple:
        with self.lock:
            return self.state, self.key

    def run(self, stop: threading.Event) -> None:
        try:
            # A key already down when the capture starts (the click or the key that started it) must be
            # released first, or it would be taken at once.
            held = {name for name, code in self.catalogue.items() if self.keys.pressed(code)}
            deadline = self.clock() + self.max_s
            while not stop.wait(self.poll_s):
                if self.clock() >= deadline:
                    return self.finish("timeout", None)
                if not self.keys.focused():
                    continue
                for name, code in self.catalogue.items():
                    down = self.keys.pressed(code)
                    if name in held:
                        if not down:
                            held.discard(name)
                    elif down:
                        return self.finish("cancelled", None) if name == self.cancel_key else self.finish("done", name)
            self.finish("cancelled", None)
        except Exception:
            # An error must end the capture visibly, never leave it waiting for ever.
            self.finish("failed", None)

    def finish(self, state: str, key) -> None:
        # The service records the key before the page can read "done", so its next model already holds it.
        try:
            self.on_end(self.ident, state, key)
        finally:
            with self.lock:
                self.state, self.key = state, key
