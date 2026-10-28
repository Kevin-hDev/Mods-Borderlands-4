# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of game_thread.py with the real Windows API, off the game: a thread of the test plays the game thread
and runs a message loop as the game does (PeekMessage, then DispatchMessage). Proves our window and queue, not that
the game's loop dispatches to them: that is the in-game question. python test_game_thread.py"""

import ctypes
import sys
import threading
import time
from ctypes import wintypes

import package_path  # noqa: F401  (before the package's modules)
import game_thread

FAILURES = []
PM_REMOVE = 1


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class Pump:
    """The stand-in game thread: creates the queue on itself, then pumps until told to stop."""

    def __init__(self, max_tasks=4, held=None):
        self.max_tasks = max_tasks
        self.held = held
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.errors = []
        self.queue = None
        self.native_id = None
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.ready.wait(5)

    def run(self):
        user32 = ctypes.WinDLL("user32")
        user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
                                        wintypes.UINT]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        self.native_id = threading.get_native_id()
        self.queue = game_thread.GameThread(self.max_tasks, self.errors.append)
        self.ready.set()
        message = wintypes.MSG()
        while not self.stop.is_set():
            if self.held is not None:
                self.held.wait(5)
            while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
            time.sleep(0.001)
        if not self.queue.closed:
            self.queue.close()

    def finish(self):
        self.stop.set()
        if self.held is not None:
            self.held.set()
        self.thread.join(5)


def wait_for(test, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if test():
            return True
        time.sleep(0.005)
    return test()


def test_runs_on_its_thread():
    pump = Pump()
    seen = []
    check("posted from another thread", pump.queue.post(lambda: seen.append(threading.get_native_id())))
    check("task ran", wait_for(lambda: len(seen) == 1))
    check("task ran on the pump's thread", seen == [pump.native_id] and seen[0] != threading.get_native_id())
    pump.finish()


def test_bounded_and_coalesced():
    held = threading.Event()
    pump = Pump(max_tasks=3, held=held)
    ran = []
    accepted = [pump.queue.post(lambda index=index: ran.append(index)) for index in range(5)]
    check("queue bounded", accepted == [True, True, True, False, False])
    held.set()
    check("all waiting tasks ran, in order", wait_for(lambda: ran == [0, 1, 2]))
    check("one message for the waiting tasks", pump.queue.messages == 1)
    pump.finish()


def test_errors_stay_inside():
    pump = Pump()
    after = []

    def broken():
        raise ValueError("task")

    pump.queue.post(broken)
    pump.queue.post(lambda: after.append(True))
    check("a failing task does not stop the next", wait_for(lambda: after == [True]))
    check("the failure is counted and reported", pump.queue.errors == 1 and pump.errors == ["ValueError"])
    pump.finish()


def test_closed():
    pump = Pump()
    done = []
    pump.queue.post(lambda: (pump.queue.close(), done.append(True)))
    check("closed from its own task", wait_for(lambda: done == [True]))
    check("no post after close", pump.queue.post(lambda: None) is False)
    pump.finish()


def main():
    test_runs_on_its_thread()
    test_bounded_and_coalesced()
    test_errors_stay_inside()
    test_closed()
    print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


main()
