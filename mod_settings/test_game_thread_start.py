# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of game_thread_start.py with the real Windows API, off the game: a thread of the test plays the game's
thread and pumps messages as the game does (PeekMessage, then DispatchMessage). python test_game_thread_start.py"""

import ctypes
import sys
import threading
import time
from ctypes import wintypes

import package_path  # noqa: F401  (before the package's modules)
import game_thread_start

FAILURES = []
PM_REMOVE = 1


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class Pump:
    """A thread that only pumps its messages, as the game's loop does each frame. With go given, it reads none until
    go is set, as the game's thread reads none while the SDK's load thread runs."""

    def __init__(self, go=None):
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.go = go
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.ready.wait(5)

    def run(self):
        user32 = ctypes.WinDLL("user32")
        message = wintypes.MSG()
        self.native_id = threading.get_native_id()
        # A thread has a message queue once it calls a message function: made before the test posts to it.
        user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
        self.ready.set()
        if self.go is not None:
            self.go.wait(5)
        while not self.stop.is_set():
            while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
            time.sleep(0.005)

    def end(self):
        self.stop.set()
        self.thread.join(2)


def wait_for(condition, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end and not condition():
        time.sleep(0.01)
    return condition()


LONG = 5.0
timeouts = []


def start_on(thread_id, task, errors, timeout_s=LONG):
    return game_thread_start.OnThread(thread_id, task, errors.append, timeout_s, lambda: timeouts.append(thread_id))


check("main thread found: the test's own first thread",
      game_thread_start.main_thread_id() == threading.main_thread().native_id)

pump = Pump()
ran, errors = [], []
runner = start_on(pump.native_id, lambda: ran.append(threading.get_native_id()), errors)
check("task runs on the target thread, from another one", wait_for(lambda: ran == [pump.native_id]))
check("hook removed after its first call", runner.hook is None and runner.done)
check("the thread that set the hook ends once it ran", wait_for(lambda: not runner.keeper.is_alive()))
time.sleep(0.1)
check("task runs once", ran == [pump.native_id] and errors == [])

failing = start_on(pump.native_id, lambda: 1 / 0, errors)
check("an error in the task is told, never raised into the loop", wait_for(lambda: errors == ["ZeroDivisionError"]))
check("the loop goes on after it", pump.thread.is_alive())

later = []
cancelled = start_on(pump.native_id, lambda: later.append(True), errors)
cancelled.cancel()
time.sleep(0.2)
check("a cancelled start never runs", later == [] and cancelled.hook is None)
check("a cancelled start ends its thread", wait_for(lambda: not cancelled.keeper.is_alive()))
pump.end()

# The SDK loads the mods on a thread that ends right after the last import, before the game's thread reads its
# next message (review, 26 October 2026). Windows removes a hook with the thread that set it: the start must not
# depend on the caller's thread living on.
go = threading.Event()
held = Pump(go)
late, made = [], []
creator = threading.Thread(target=lambda: made.append(start_on(held.native_id, lambda: late.append(True), errors)))
creator.start()
creator.join(5)
check("the creating thread has ended before any message is read", not creator.is_alive() and len(made) == 1)
go.set()
check("the task still runs on the game's thread", wait_for(lambda: late == [True]))
held.end()

silent = Pump(threading.Event())
never = []
timed = start_on(silent.native_id, lambda: never.append(True), errors, timeout_s=0.3)
check("a thread that never reads its messages: the timeout is told",
      wait_for(lambda: timeouts == [silent.native_id]))
check("then the hook is removed and the task never runs", timed.hook is None and never == [])
silent.go.set()
time.sleep(0.1)
check("still never runs once the thread reads again", never == [])
silent.end()

# The deadline and the game's message at the same instant (second review): the hook runs between the keeper's
# decision and the hook's removal. A stand-in Windows lets the test run the hook in that gap: the task then runs, or
# the timeout is told, never both.


class StandInWindows:
    def __init__(self):
        self.unhooked = 0

    def SetWindowsHookExW(self, *_args):
        return 1

    def PostThreadMessageW(self, *_args):
        return 1

    def UnhookWindowsHookEx(self, _hook):
        self.unhooked += 1

    def CallNextHookEx(self, *_args):
        return 0

    def GetCurrentThreadId(self):
        return 42


class HookInTheGap(game_thread_start.OnThread):
    def cancel(self):
        if threading.current_thread() is self.keeper and not getattr(self, "raced", False):
            self.raced = True
            self.called(0, 0, 0)
        super().cancel()


windows = StandInWindows()
told, gap_ran = [], []
gap = HookInTheGap(42, lambda: gap_ran.append(True), errors.append, 0.2, lambda: told.append(True),
                   api=(windows, windows))
check("deadline and message at once: the task or the timeout, never both",
      wait_for(lambda: not gap.keeper.is_alive()) and len(gap_ran) + len(told) == 1 and windows.unhooked == 1)

try:
    start_on(0xFFFFFFF0, lambda: None, errors)
    check("an unknown thread is refused", False)
except OSError:
    check("an unknown thread is refused", True)

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
